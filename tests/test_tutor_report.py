"""AI tutor, explanation and PDF tests (5 号). Synthetic fixtures only; no external API is ever called.

Provider responses are simulated with httpx.MockTransport. Tests patch the environment so a local .env
cannot change the outcome.
"""
import importlib.util, json, os, unittest
from unittest.mock import patch
AVAILABLE=all(importlib.util.find_spec(m) for m in ['fastapi','scipy','statsmodels','httpx','reportlab','dotenv'])
KEY='sk-test-DO-NOT-LOG-123'

def synthetic_rows(base=25.,step=.02,n=25,start=2001):
 """Synthetic teaching fixture, not NASA data."""
 return [{'year':start+i,'value':base+step*i+(.03 if i%2 else -.03)} for i in range(n)]

def make_result(variable='T2M',rows=None,unit='C'):
 from app.analysis import analyze
 from app.data import source_url
 rows=synthetic_rows() if rows is None else rows
 settings={'city':'Singapore','variable':variable,'start':2001,'end':2025}
 try: stats,error=analyze(rows),None
 except ValueError as e: stats,error=None,str(e)
 return settings,{'settings':settings,'annual':rows,'excluded_years':[],'source_unit':unit,'unit':unit,'aggregation':'Synthetic test aggregation','source_url':source_url(settings),'source_header':{},'stats':stats,'analysis_error':error,'retrieved_at':'2026-01-01T00:00:00Z'}

def chat(content):
 return {'choices':[{'message':{'role':'assistant','content':content}}]}

class ProviderHarness(unittest.TestCase):
 """Shared fake-provider helpers; holds no tests itself."""
 def setUp(self):
  from fastapi.testclient import TestClient
  from app.main import app
  self.client=TestClient(app,raise_server_exceptions=True); self.requests=[]
 def call(self,handler,body=None,env=None):
  """Run /api/tutor with a fake provider. handler(request, attempt) returns an httpx.Response or raises."""
  import httpx
  real=httpx.AsyncClient
  def recorder(request):
   self.requests.append(json.loads(request.content)); return handler(request,len(self.requests))
  def factory(*args,**kwargs):
   kwargs['transport']=httpx.MockTransport(recorder); return real(*args,**kwargs)
  environment={'LLM_API_KEY':KEY,'LLM_TOKEN_PARAM':'','LLM_BASE_URL':'https://provider.invalid/v1','LLM_MODEL':'test-model',**(env or {})}
  with patch.dict(os.environ,environment), patch('app.main.httpx.AsyncClient',factory):
   with self.assertLogs('climatelens.tutor',level='INFO') as logs:
    import logging; logging.getLogger('climatelens.tutor').info('test marker')
    response=self.client.post('/api/tutor',json=body or {'conclusion':'Temperature increased.'})
  self.assertEqual(response.status_code,200,response.text)
  self.assertNotIn(KEY,'\n'.join(logs.output)); self.assertNotIn(KEY,response.text)
  return response.json(),logs.output
 def assertFallback(self,handler,reason,status='-'):
  data,logs=self.call(handler)
  self.assertEqual(data['mode'],'deterministic fallback'); self.assertEqual(data['reason'],reason)
  self.assertIn('check five things',data['text'])
  self.assertTrue(any(f'reason={reason}' in line and f'status={status}' in line for line in logs),logs)
  return data

@unittest.skipUnless(AVAILABLE,'Install requirements.txt to run AI tutor and PDF tests')
class TutorProviderTests(ProviderHarness):
 def test_success(self):
  import httpx
  data,_=self.call(lambda request,n: httpx.Response(200,json=chat('Cite the slope and its interval.')))
  self.assertEqual(data['text'],'Cite the slope and its interval.'); self.assertIn('AI advisory',data['mode'])
  self.assertNotIn('reason',data); self.assertIn('verified_summary',data)
  self.assertEqual(self.requests[0]['max_tokens'],600); self.assertEqual(self.requests[0]['temperature'],.2)
 def test_no_key_reason(self):
  with patch.dict(os.environ,{'LLM_API_KEY':''}): data=self.client.post('/api/tutor',json={}).json()
  self.assertEqual(data['mode'],'deterministic'); self.assertEqual(data['reason'],'no_key')
 def test_timeout(self):
  import httpx
  def handler(request,n): raise httpx.ReadTimeout('timed out',request=request)
  self.assertFallback(handler,'timeout')
 def test_connection_error(self):
  import httpx
  def handler(request,n): raise httpx.ConnectError('refused',request=request)
  self.assertFallback(handler,'http_error')
 def test_invalid_key(self):
  import httpx
  self.assertFallback(lambda request,n: httpx.Response(401,json={'error':{'message':'Incorrect API key provided: '+KEY}}),'auth',401)
 def test_forbidden(self):
  import httpx
  self.assertFallback(lambda request,n: httpx.Response(403,json={'error':'forbidden'}),'auth',403)
 def test_provider_500(self):
  import httpx
  self.assertFallback(lambda request,n: httpx.Response(500,text='upstream exploded'),'http_error',500)
 def test_rate_limited(self):
  import httpx
  self.assertFallback(lambda request,n: httpx.Response(429,json={'error':'slow down'}),'http_error',429)
 def test_non_json(self):
  import httpx
  self.assertFallback(lambda request,n: httpx.Response(200,text='<html>gateway</html>'),'bad_response')
 def test_malformed_payloads(self):
  import httpx
  shapes=[{'choices':None},{'choices':[]},{'choices':[None]},{'choices':[{}]},{'choices':[{'message':None}]},{'choices':'text'},[1,2],None,'just a string',
   chat(None),chat(''),chat('   '),chat(['not','a','string']),chat({'text':'nested'}),{'error':{'message':'no choices'}}]
  for shape in shapes:
   with self.subTest(shape=shape): self.assertFallback(lambda request,n,shape=shape: httpx.Response(200,json=shape),'bad_response')
 def test_bad_base_url_scheme(self):
  import httpx
  with patch.dict(os.environ,{'LLM_API_KEY':KEY,'LLM_TOKEN_PARAM':'','LLM_BASE_URL':'provider.invalid/v1'}), self.assertLogs('climatelens.tutor') as logs:
   data=self.client.post('/api/tutor',json={}).json()
  self.assertEqual(data['mode'],'deterministic fallback'); self.assertEqual(data['reason'],'http_error')
  self.assertIn('error=UnsupportedProtocol',logs.output[0]); self.assertNotIn(KEY,logs.output[0])

@unittest.skipUnless(AVAILABLE,'Install requirements.txt to run AI tutor and PDF tests')
class TokenParameterRetryTests(ProviderHarness):
 """400 retry: once, only when the error names max_tokens or temperature; manual LLM_TOKEN_PARAM disables token switching."""
 def test_retry_on_max_tokens_error(self):
  import httpx
  def handler(request,n):
   if n==1: return httpx.Response(400,json={'error':{'message':"Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."}})
   return httpx.Response(200,json=chat('ok after retry'))
  data,logs=self.call(handler)
  self.assertEqual(data['text'],'ok after retry'); self.assertEqual(len(self.requests),2)
  self.assertIn('max_tokens',self.requests[0]); self.assertNotIn('max_tokens',self.requests[1])
  self.assertEqual(self.requests[1]['max_completion_tokens'],600); self.assertNotIn('temperature',self.requests[1])
 def test_retry_on_temperature_error_keeps_token_param(self):
  import httpx
  def handler(request,n):
   if n==1: return httpx.Response(400,json={'error':{'message':"Unsupported value: 'temperature' does not support 0.2 with this model."}})
   return httpx.Response(200,json=chat('ok'))
  data,_=self.call(handler)
  self.assertEqual(data['text'],'ok'); self.assertEqual(len(self.requests),2)
  self.assertNotIn('temperature',self.requests[1]); self.assertEqual(self.requests[1]['max_tokens'],600)
 def test_no_retry_for_unrelated_400(self):
  import httpx
  data,_=self.call(lambda request,n: httpx.Response(400,json={'error':{'message':'Invalid model name'}}))
  self.assertEqual(len(self.requests),1); self.assertEqual(data['reason'],'http_error')
 def test_retry_at_most_once(self):
  import httpx
  data,_=self.call(lambda request,n: httpx.Response(400,json={'error':{'message':'max_tokens and temperature unsupported'}}))
  self.assertEqual(len(self.requests),2); self.assertEqual(data['reason'],'http_error')
 def test_manual_param_disables_token_switch(self):
  import httpx
  data,_=self.call(lambda request,n: httpx.Response(400,json={'error':{'message':"Unsupported parameter: 'max_tokens'"}}),env={'LLM_TOKEN_PARAM':'max_tokens'})
  self.assertEqual(len(self.requests),1); self.assertEqual(data['reason'],'http_error')
 def test_manual_max_completion_tokens_used_first(self):
  import httpx
  data,_=self.call(lambda request,n: httpx.Response(200,json=chat('ok')),env={'LLM_TOKEN_PARAM':'max_completion_tokens'})
  self.assertEqual(self.requests[0]['max_completion_tokens'],600); self.assertNotIn('max_tokens',self.requests[0])

if __name__=='__main__': unittest.main()
