"""Synthetic upstream responses: verify data failures become HTTP 503, not 500."""
import importlib.util, unittest
from unittest.mock import patch
AVAILABLE = all(importlib.util.find_spec(m) for m in ["fastapi", "httpx", "statsmodels", "scipy", "dotenv"])


@unittest.skipUnless(AVAILABLE, "Install requirements.txt to run data API tests")
class DataAPITests(unittest.TestCase):
    def test_malformed_and_unverified_upstream_responses(self):
        import httpx
        from fastapi.testclient import TestClient
        from app.main import app, CACHE
        original_client = httpx.AsyncClient
        settings = dict(city='Singapore', variable='T2M', start=2001, end=2025)
        for payload in [[], {'parameters': None},
                        {'parameters': {'T2M': {'units': 'F'}}, 'properties': {}},
                        {'parameters': {'T2M': {'units': 'C'}},
                         'properties': {'parameter': []}}]:
            with self.subTest(payload=payload):
                CACHE.clear()
                transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
                def factory(*args, **kwargs):
                    return original_client(*args, transport=transport, **kwargs)
                with TestClient(app) as client, patch('app.main.httpx.AsyncClient', factory):
                    response = client.post('/api/investigate', json=settings)
                self.assertEqual(response.status_code, 503, response.text)
                self.assertIn('NASA could not provide a validated response', response.json()['detail'])
        CACHE.clear()
