"""Dependency-backed tests. Synthetic fixtures only. Live NASA test is opt-in."""
import importlib.util, os, unittest
AVAILABLE=all(importlib.util.find_spec(m) for m in ['fastapi','scipy','statsmodels','httpx','reportlab','dotenv'])
@unittest.skipUnless(AVAILABLE,'Install requirements.txt to run scientific, API and PDF tests')
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  from fastapi.testclient import TestClient
  from app.main import app
  self.client=TestClient(app)
 def test_scientific_direction_and_uncertainty(self):
  from app.analysis import analyze
  from scipy.stats import linregress
  for sign in [1,-1]:
   rows=[{'year':2001+i,'value':25+sign*.1*i+(.03 if i%2 else -.03)} for i in range(25)]
   r=analyze(rows);reference=linregress([x['year'] for x in rows],[x['value'] for x in rows])
   self.assertAlmostEqual(r['slope_year'],reference.slope,places=10)
   self.assertTrue(r['significant']);self.assertLess(r['ci95_year'][0],r['slope_year']);self.assertGreater(r['ci95_year'][1],r['slope_year'])
 def test_hac_uncertainty_against_independent_calculation(self):
    from math import sqrt
    from statistics import mean

    from scipy.stats import t

    from app.analysis import analyze
    values = [24.9, 25.2, 25.5, 25.4, 25.0, 24.8,
              24.9, 25.3, 25.7, 25.9, 25.6, 25.5]
    rows = [
        {"year": 2001 + i, "value": value}
        for i, value in enumerate(values)
    ]
    n = len(values)
    lag = 2
    df = n - 2

    centered_years = [i - (n - 1) / 2 for i in range(n)]
    mean_value = mean(values)
    sum_squares = sum(x**2 for x in centered_years)
    slope = sum(
        x * (value - mean_value)
        for x, value in zip(centered_years, values)
    ) / sum_squares
    scores = [
        x * (value - mean_value - slope * x)
        for x, value in zip(centered_years, values)
    ]

    weighted_sum = sum(score**2 for score in scores)
    for offset in range(1, lag + 1):
        weight = 1 - offset / (lag + 1)
        weighted_sum += 2 * weight * sum(
            scores[i] * scores[i - offset] for i in range(offset, n)
        )

    expected_se = sqrt((n / df) * weighted_sum / sum_squares**2)
    critical_value = t.ppf(0.975, df)
    margin = critical_value * expected_se
    expected_p = 2 * t.sf(abs(slope / expected_se), df)

    result = analyze(rows)
    lower, upper = result["ci95_year"]
    actual_se = (upper - lower) / (2 * critical_value)

    self.assertEqual(result["hac_lags"], lag)
    self.assertAlmostEqual(result["slope_year"], slope, places=10)
    self.assertAlmostEqual(result["slope_decade"], 10 * slope, places=10)
    self.assertAlmostEqual(actual_se, expected_se, places=10)
    self.assertAlmostEqual(result["p_value"], expected_p, places=10)
    self.assertAlmostEqual(lower, slope - margin, places=10)
    self.assertAlmostEqual(upper, slope + margin, places=10)
 def test_stable_nonsignificant(self):
  from app.analysis import analyze
  r=analyze([{'year':2001+i,'value':20+(-1)**i*.3} for i in range(25)])
  self.assertFalse(r['significant'])
 def test_gap_and_insufficient(self):
  from app.analysis import analyze
  with self.assertRaises(ValueError):analyze([{'year':2001+i,'value':i} for i in range(5)])
  with self.assertRaises(ValueError):analyze([{'year':2001+2*i,'value':i} for i in range(15)])
 def test_interpret_ambiguity(self):
  r=self.client.post('/api/interpret',json={'question':'Compare Singapore and Jakarta temperature 2001 to 2025'}).json()
  self.assertIsNone(r['proposed']['city']);self.assertTrue(r['needs_review'])
 def test_pdf_incomplete_and_escaping(self):
  r=self.client.post('/api/report',json={'conclusion':'<b>Student claim</b> 中文'})
  self.assertEqual(r.status_code,200);self.assertTrue(r.content.startswith(b'%PDF-'));self.assertIn(b'%%EOF',r.content)
 def test_no_key_fallback(self):
  from unittest.mock import patch
  with patch.dict(os.environ,{'LLM_API_KEY':''}):r=self.client.post('/api/tutor',json={})
  self.assertEqual(r.json()['mode'],'deterministic')
 def test_settings_mismatch(self):
  from app.main import RESULTS
  RESULTS['test']={'settings':{'city':'Singapore','variable':'T2M','start':2001,'end':2025}}
  r=self.client.post('/api/report',json={'result_id':'test','settings':{'city':'Bangkok','variable':'T2M','start':2001,'end':2025}})
  self.assertEqual(r.status_code,409);RESULTS.pop('test')
 @unittest.skipUnless(os.getenv('RUN_LIVE_NASA')=='1','Live NASA test requires explicit opt-in and network')
 def test_live_singapore(self):
  r=self.client.post('/api/investigate',json={'city':'Singapore','variable':'T2M','start':2001,'end':2025})
  self.assertEqual(r.status_code,200,r.text);self.assertEqual(len(r.json()['annual']),25);self.assertIsNotNone(r.json()['stats'])