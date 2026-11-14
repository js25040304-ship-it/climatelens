"""Question interpretation prepares parameters; it never executes analysis."""
import re
from .data import CITIES

def parse_question(q):
 text=q.lower(); cities=[c for c in CITIES if c.lower() in text]
 aliases={'T2M':['temperature','hot','warm','温度','热'],'PRECTOTCORR':['rain','precipitation','降雨'],'RH2M':['humidity','湿度'],'WS10M':['wind','风速'],'ALLSKY_SFC_SW_DWN':['solar','radiation','太阳','辐射']}
 variables=[k for k,words in aliases.items() if any(w in text for w in words)]
 years=[int(v) for v in re.findall(r'\b(?:19|20)\d{2}\b',text)]
 candidate={'city':cities[0] if len(cities)==1 else None,'variable':variables[0] if len(variables)==1 else None,'start':min(years) if len(years)==2 else None,'end':max(years) if len(years)==2 else None}
 return {'proposed':candidate,'needs_review':True,'message':'Confirm every field before running. Unrecognized or ambiguous fields remain unset; unsupported requests are not automatically analyzed.'}

