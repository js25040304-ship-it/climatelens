"""All values in this file are synthetic test fixtures, never production data."""
import copy, unittest
from app.data import normalize, validate, source_url

S={'city':'Singapore','variable':'T2M','start':2001,'end':2010}
def fixture(variable='T2M',unit='C',value=20):
 return {'parameters':{variable:{'units':unit}},'header':{'fill_value':-999},'properties':{'parameter':{variable:{f'{y}{m:02d}':value for y in range(2001,2011) for m in range(1,13)}}}}
class DataTests(unittest.TestCase):
 def test_complete_mean(self):
  r=normalize(fixture(),S);self.assertEqual(len(r['annual']),10);self.assertEqual(r['annual'][0]['value'],20)
 def test_day_weighting(self):
  p=fixture(value=0);p['properties']['parameter']['T2M']['200101']=31
  self.assertAlmostEqual(normalize(p,S)['annual'][0]['value'],31*31/365)
 def test_leap_precipitation(self):
  s={**S,'variable':'PRECTOTCORR'};r=normalize(fixture('PRECTOTCORR','mm/day',1),s)
  self.assertEqual(r['annual'][0]['value'],365);self.assertEqual(r['annual'][3]['value'],366)
 def test_missing_year_excluded(self):
  p=fixture();del p['properties']['parameter']['T2M']['200105'];r=normalize(p,S)
  self.assertEqual(len(r['annual']),9);self.assertEqual(r['excluded_years'][0]['missing_or_invalid_months'],[5])
 def test_invalid_values(self):
  for value in [-999,float('nan'),float('inf'),None,'20',True]:
   with self.subTest(value=value):
    p=fixture();p['properties']['parameter']['T2M']['200101']=value
    self.assertEqual(len(normalize(p,S)['annual']),9)
 def test_wrong_units(self):
  with self.assertRaises(ValueError): normalize(fixture(unit='F'),S)
 def test_annual_13_ignored(self):
  p=fixture();p['properties']['parameter']['T2M']['200113']=10000
  self.assertEqual(normalize(p,S)['annual'][0]['value'],20)
 def test_humidity_bounds(self):
  self.assertEqual(normalize(fixture('RH2M','%',101),{**S,'variable':'RH2M'})['annual'],[])
 def test_nonnegative_variables(self):
  for v,u in [('WS10M','m/s'),('ALLSKY_SFC_SW_DWN','kW-hr/m^2/day'),('PRECTOTCORR','mm/day')]:
   self.assertEqual(normalize(fixture(v,u,-1),{**S,'variable':v})['annual'],[])
 def test_all_units(self):
  for v,u in [('WS10M','m/s'),('RH2M','%'),('ALLSKY_SFC_SW_DWN','kW-hr/m^2/day')]:
   self.assertEqual(len(normalize(fixture(v,u,10),{**S,'variable':v})['annual']),10)
 def test_invalid_settings(self):
  for change in [{'city':'unknown'},{'variable':'unknown'},{'start':2009},{'end':2099},{'start':2001.0}]:
   with self.assertRaises(ValueError):validate({**S,**change})
 def test_source(self):
  url=source_url(S);self.assertTrue(url.startswith('https://power.larc.nasa.gov/'));self.assertIn('latitude=1.3521',url);self.assertIn('community=RE',url)

if __name__=='__main__':unittest.main()
