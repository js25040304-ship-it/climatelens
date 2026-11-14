"""Owner 1: catalog, question and investigation integration routes."""
import hashlib
import json
import secrets
import time
from functools import lru_cache
from pathlib import Path
import httpx
from fastapi import APIRouter, HTTPException
from .schemas import Settings, Question
from .data import CITIES, VARIABLES, validate, source_url, normalize
from .analysis import analyze
from .questions import parse_question
from .state import RESULTS, CACHE

router = APIRouter()
ARCHIVE_DIR = Path(__file__).resolve().parents[1] / 'evidence/nasa-data/20261114T080209845385Z'


@lru_cache(maxsize=1)
def archive_index():
    rows = json.loads((ARCHIVE_DIR / 'coverage.json').read_text(encoding='utf-8'))
    return {row['source_url']: row for row in rows if row['success']}


def archived_response(url):
    row = archive_index().get(url)
    if row is None:
        raise ValueError('No verified archive exists for this city, indicator and period.')
    raw = (ARCHIVE_DIR / row['raw_file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('The archived NASA response failed its integrity check.')
    saved_result = ARCHIVE_DIR / 'results' / Path(row['raw_file']).name
    retrieved_at = json.loads(saved_result.read_text(encoding='utf-8'))['retrieved_at']
    return json.loads(raw), retrieved_at


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
  cached=CACHE.get(url)
  if cached and time.time()-cached[0]<3600:
   retrieved,payload=cached
   data=normalize(payload,s)
   source_mode='cache'
  else:
   try:
    async with httpx.AsyncClient(timeout=45) as client:
     response=await client.get(url)
    response.raise_for_status()
   except (httpx.RequestError,ImportError):
    payload,retrieved_at=archived_response(url)
    data=normalize(payload,s)
    source_mode='archive'
   else:
    payload=response.json()
    data=normalize(payload,s)
    retrieved=time.time()
    if len(CACHE)>=100: CACHE.pop(next(iter(CACHE)))
    CACHE[url]=(retrieved,payload)
    source_mode='live'
  if source_mode!='archive':
   retrieved_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(retrieved))
 except (httpx.HTTPError,ImportError,OSError,ValueError,KeyError,TypeError) as e:
  raise HTTPException(503,'Analysis unavailable: NASA could not provide a validated response. '+str(e)[:200])
 error=None
 try: stats=analyze(data['annual'])
 except ValueError as e: stats=None; error=str(e)
 result={'settings':s,**data,'stats':stats,'analysis_error':error,'source_mode':source_mode,'retrieved_at':retrieved_at}
 if len(RESULTS)>=200: RESULTS.pop(next(iter(RESULTS)))
 identifier=secrets.token_urlsafe(24); RESULTS[identifier]=result
 return {'id':identifier,**result}

