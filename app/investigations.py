"""Owner 1: catalog, question and investigation integration routes."""
import time
import secrets
import httpx
from fastapi import APIRouter, HTTPException
from .schemas import Settings, Question
from .data import CITIES, VARIABLES, validate, source_url, normalize
from .analysis import analyze
from .questions import parse_question
from .state import RESULTS, CACHE

router = APIRouter()

@router.get('/api/catalog')
def catalog(): return {'cities':CITIES,'variables':VARIABLES,'availability':'Candidate combinations are validated on each NASA response; no preverified coverage is claimed.'}


@router.post('/api/interpret')
def interpret(q:Question): return parse_question(q.question)


@router.post('/api/investigate')
async def investigate(request:Settings):
 try: s=validate(request.model_dump())
 except ValueError as e: raise HTTPException(422,str(e))
 url=source_url(s)
 try:
  if url in CACHE and time.time()-CACHE[url][0]<3600: payload=CACHE[url][1]
  else:
   async with httpx.AsyncClient(timeout=45) as client:
    response=await client.get(url); response.raise_for_status(); payload=response.json()
   if len(CACHE)>=100: CACHE.pop(next(iter(CACHE)))
   CACHE[url]=(time.time(),payload)
  data=normalize(payload,s)
 except (httpx.HTTPError,ValueError,KeyError,TypeError) as e:
  raise HTTPException(503,'Analysis unavailable: NASA could not provide a validated response. Check connectivity, variable and period. '+str(e)[:200])
 error=None
 try: stats=analyze(data['annual'])
 except ValueError as e: stats=None; error=str(e)
 result={'settings':s,**data,'stats':stats,'analysis_error':error,'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(CACHE[url][0]))}
 if len(RESULTS)>=200: RESULTS.pop(next(iter(RESULTS)))
 identifier=secrets.token_urlsafe(24); RESULTS[identifier]=result
 return {'id':identifier,**result}

