"""Cross-module contract tests; NASA values here are synthetic and explicitly mocked."""
import os
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.data import source_url
from app.state import RESULTS, CACHE

SETTINGS = {'city': 'Singapore', 'variable': 'T2M', 'start': 2001, 'end': 2025}

def synthetic_response():
    return {'parameters': {'T2M': {'units': 'C'}}, 'header': {'fill_value': -999},
            'properties': {'parameter': {'T2M': {
                f'{year}{month:02d}': 25 + (year-2001)*0.05 + ((year % 3)-1)*0.02
                for year in range(2001, 2026) for month in range(1, 13)}}}}

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        RESULTS.clear()
        CACHE.clear()

    def tearDown(self):
        RESULTS.clear()
        CACHE.clear()

    def test_route_contracts_and_static_page(self):
        schema = self.client.get('/openapi.json').json()
        for path in ['/api/interpret', '/api/investigate', '/api/tutor', '/api/report']:
            self.assertIn('post', schema['paths'][path])
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ok')
        root = self.client.get('/')
        self.assertEqual(root.status_code, 200)
        # Root is the five-island entry; the base tag keeps its relative assets working from '/'.
        self.assertIn('ringStage', root.text)
        self.assertIn('<base href="/static/lens/">', root.text)
        self.assertEqual(self.client.get('/static/lens/ring.js').status_code, 200)
        lab = self.client.get('/static/lens/singapore/index.html')
        self.assertEqual(lab.status_code, 200)
        self.assertIn('Singapore island lab', lab.text)
        for page in ['Discover', 'Explore map', 'Evidence', 'My notebook', 'Data & methods']:
            self.assertIn(page, lab.text)
        # The classic five-chapter investigation keeps its own URL.
        self.assertIn('ClimateLens', self.client.get('/static/index.html').text)
        self.assertEqual(self.client.get('/static/app.js').status_code, 200)

    def test_mocked_investigation_to_tutor_and_report(self):
        CACHE[source_url(SETTINGS)] = (time.time(), synthetic_response())
        response = self.client.post('/api/investigate', json=SETTINGS)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(len(result['annual']), 25)
        self.assertIsNotNone(result['stats'])
        body = {'settings': SETTINGS, 'result_id': result['id'], 'reviewed': True,
                'question': 'Synthetic test only', 'conclusion': 'A positive trend is estimated, without establishing a cause.'}
        with patch.dict(os.environ, {'LLM_API_KEY': ''}):
            tutor = self.client.post('/api/tutor', json=body)
        self.assertEqual(tutor.status_code, 200)
        self.assertEqual(tutor.json()['mode'], 'deterministic')
        pdf = self.client.post('/api/report', json=body)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF-'))
        self.assertEqual(RESULTS[result['id']]['stats'], result['stats'])

    def test_report_comparison_requires_matching_evidence(self):
        other_settings = {**SETTINGS, 'city': 'Bangkok'}
        for settings in (SETTINGS, other_settings):
            CACHE[source_url(settings)] = (time.time(), synthetic_response())
        primary = self.client.post('/api/investigate', json=SETTINGS).json()
        secondary = self.client.post('/api/investigate', json=other_settings).json()
        body = {'settings': SETTINGS, 'result_id': primary['id'], 'comparison_result_id': secondary['id']}
        self.assertEqual(self.client.post('/api/report', json=body).status_code, 200)

        invalid = self.client.post('/api/report', json={**body, 'comparison_result_id': primary['id']})
        self.assertEqual(invalid.status_code, 409)
        RESULTS[secondary['id']]['annual'] = secondary['annual'][1:]
        mismatch = self.client.post('/api/report', json=body)
        self.assertEqual(mismatch.status_code, 409)
        self.assertIn('same complete years', mismatch.json()['detail'])
        RESULTS.pop(secondary['id'])
        self.assertEqual(self.client.post('/api/report', json=body).status_code, 410)

    def test_upstream_failure_produces_no_result(self):
        import httpx
        with patch('app.investigations.httpx.AsyncClient.get', new=AsyncMock(side_effect=httpx.ConnectError('offline'))):
            response = self.client.post('/api/investigate', json={**SETTINGS, 'end': 2024})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(RESULTS, {})

    def test_connection_failure_uses_the_verified_humidity_archive(self):
        import httpx
        from app.investigations import archived_response

        settings = {**SETTINGS, 'city': 'Kuala Lumpur', 'variable': 'RH2M'}
        url = source_url(settings)
        failures = (
            httpx.ConnectError('offline'),
            httpx.ReadTimeout('slow upstream'),
            TimeoutError('request deadline'),
            429, 500, 502, 503, 504,
        )
        for failure in failures:
            with self.subTest(failure=failure):
                mock = (AsyncMock(return_value=httpx.Response(failure, request=httpx.Request('GET', url)))
                        if isinstance(failure, int) else AsyncMock(side_effect=failure))
                with patch('app.investigations.httpx.AsyncClient.get', new=mock):
                    response = self.client.post('/api/investigate', json=settings)
                self.assertEqual(response.status_code, 200, response.text)
                result = response.json()
                self.assertEqual(result['source_mode'], 'archive')
                self.assertEqual(result['retrieved_at'], archived_response(url)[1])
                self.assertEqual(len(result['annual']), 25)
                self.assertNotIn(url, CACHE)

        rejected = httpx.Response(404, request=httpx.Request('GET', url))
        with patch('app.investigations.httpx.AsyncClient.get', new=AsyncMock(return_value=rejected)):
            self.assertEqual(self.client.post('/api/investigate', json=settings).status_code, 503)

    def test_expired_result(self):
        for endpoint in ['report', 'tutor']:
            response = self.client.post('/api/' + endpoint, json={'result_id': 'expired', 'settings': SETTINGS})
            self.assertEqual(response.status_code, 410)

    def test_invalid_settings_rejected_before_network(self):
        response = self.client.post('/api/investigate', json={**SETTINGS, 'city': 'Unsupported'})
        self.assertEqual(response.status_code, 422)
