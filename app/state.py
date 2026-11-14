"""Process-local result storage. Restarting the single-worker server clears it."""
from fastapi import HTTPException

RESULTS = {}
CACHE = {}

def result_for(w):
 if not w.result_id: return None
 r=RESULTS.get(w.result_id)
 if not r: raise HTTPException(410,'Investigation expired after server restart or memory eviction; run it again.')
 if r['settings']!=w.settings.model_dump(): raise HTTPException(409,'Settings changed; rerun the investigation.')
 return r

