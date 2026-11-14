"""NASA POWER monthly ingestion. No synthetic production fallback."""
import calendar
import math
from datetime import date
from urllib.parse import urlencode

CITIES = {'Singapore': (1.3521,103.8198), 'Kuala Lumpur':(3.139,101.6869), 'Jakarta':(-6.2088,106.8456), 'Bangkok':(13.7563,100.5018), 'Ho Chi Minh City':(10.8231,106.6297)}
VARIABLES = {
 'T2M': {'label':'Air temperature','unit':'C','accepted':['C'],'aggregation':'Day-weighted annual mean','definition':'Air temperature at 2 metres.'},
 'PRECTOTCORR': {'label':'Precipitation','unit':'mm/year','accepted':['mm/day'],'aggregation':'Monthly daily rate multiplied by days, then summed','definition':'Bias-corrected precipitation.'},
 'RH2M': {'label':'Relative humidity','unit':'%','accepted':['%'],'aggregation':'Day-weighted annual mean','definition':'Relative humidity at 2 metres.'},
 'WS10M': {'label':'Wind speed','unit':'m/s','accepted':['m/s'],'aggregation':'Day-weighted annual mean','definition':'Wind speed at 10 metres.'},
 'ALLSKY_SFC_SW_DWN': {'label':'Surface solar radiation','unit':'kW-hr/m^2/day','accepted':['kW-hr/m^2/day'],'aggregation':'Day-weighted mean daily energy','definition':'All-sky downward surface shortwave energy.'}}

def validate(settings):
 city, variable = settings.get('city'), settings.get('variable')
 start, end = settings.get('start'), settings.get('end')
 if city not in CITIES or variable not in VARIABLES: raise ValueError('Select a supported city and variable.')
 if type(start) is not int or type(end) is not int or not 2001 <= start <= end <= date.today().year-1: raise ValueError('Use complete calendar years from 2001 to last year.')
 if end-start < 9: raise ValueError('Select at least 10 years for this educational trend analysis.')
 return {'city':city,'variable':variable,'start':start,'end':end}

def source_url(s):
 lat,lon=CITIES[s['city']]
 return 'https://power.larc.nasa.gov/api/temporal/monthly/point?'+urlencode(dict(parameters=s['variable'],community='RE',latitude=lat,longitude=lon,start=s['start'],end=s['end'],format='JSON'))

def normalize(payload,s):
 spec=VARIABLES[s['variable']]
 meta=payload.get('parameters',{}).get(s['variable'],{})
 if meta.get('units') not in spec['accepted']: raise ValueError('NASA returned an unverified unit; analysis is disabled: '+str(meta.get('units')))
 series=payload.get('properties',{}).get('parameter',{}).get(s['variable'])
 if not isinstance(series,dict): raise ValueError('NASA response does not contain monthly observations.')
 fill=payload.get('header',{}).get('fill_value',-999)
 annual=[]; excluded=[]
 for year in range(s['start'],s['end']+1):
  weighted=0.; days=0; missing=[]
  for month in range(1,13):
   v=series.get(f'{year}{month:02d}')
   valid=isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v != fill and v != -999
   if valid and s['variable'] in ('PRECTOTCORR','WS10M','ALLSKY_SFC_SW_DWN'): valid=v>=0
   if valid and s['variable']=='RH2M': valid=0<=v<=100
   if not valid: missing.append(month); continue
   n=calendar.monthrange(year,month)[1]; weighted+=v*n; days+=n
  if missing: excluded.append({'year':year,'missing_or_invalid_months':missing})
  else: annual.append({'year':year,'value':weighted if s['variable']=='PRECTOTCORR' else weighted/days})
 return {'annual':annual,'excluded_years':excluded,'source_unit':meta['units'],'unit':spec['unit'],'aggregation':spec['aggregation'],'source_url':source_url(s),'source_header':payload.get('header',{})}
