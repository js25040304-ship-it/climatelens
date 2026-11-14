"""Opt-in live acceptance: 25 sequential real NASA/API calls, retaining evidence.
Run from the repository root: python scripts/verify_nasa_data.py --live
No synthetic fallback. Existing evidence is never overwritten.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.data import CITIES, VARIABLES, source_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Allow real network requests')
    parser.add_argument('--output', type=Path, default=Path('evidence/nasa-data'))
    args = parser.parse_args()
    if not args.live:
        parser.error('Pass --live to explicitly enable 25 serial NASA requests.')
    import httpx
    from fastapi.testclient import TestClient
    from app.main import app, CACHE
    root = args.output / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (root / 'raw').mkdir(parents=True, exist_ok=False)
    (root / 'results').mkdir()
    captured = {}

    class RecordingClient(httpx.AsyncClient):
        async def get(self, *a, **kw):
            response = await super().get(*a, **kw)
            captured['response'] = response
            return response

    rows = []
    with TestClient(app) as client, patch('app.main.httpx.AsyncClient', RecordingClient):
        for city in CITIES:
            for variable in VARIABLES:
                settings = dict(city=city, variable=variable, start=2001, end=2025)
                slug = city.lower().replace(' ', '-') + '-' + variable
                captured.clear()
                CACHE.clear()  # Every combination must make a fresh real NASA call.
                row = dict(**settings, checked_at=datetime.now(timezone.utc).isoformat(),
                           source_url=source_url(settings), source_unit='', unit='',
                           complete_years=0, success=False, error='', api_status='',
                           nasa_status='', raw_file='', sha256='')
                try:
                    response = client.post('/api/investigate', json=settings)
                    row['api_status'] = response.status_code
                    result = response.json()
                    (root / 'results' / (slug + '.json')).write_text(
                        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                    if response.status_code != 200:
                        raise ValueError(str(result))
                    row.update(source_unit=result['source_unit'], unit=result['unit'],
                               complete_years=len(result['annual']))
                    expected = list(range(2001, 2026))
                    if [r['year'] for r in result['annual']] != expected or result['excluded_years']:
                        raise ValueError('Not 25 complete calendar years: ' + str(result['excluded_years']))
                    if result['stats'] is None:
                        raise ValueError('Endpoint returned no trend inference: ' + str(result['analysis_error']))
                    row['success'] = True
                except Exception as exc:
                    row['error'] = type(exc).__name__ + ': ' + str(exc)
                finally:
                    raw_response = captured.get('response')
                    if raw_response is not None:
                        raw_name = 'raw/' + slug + '.json'
                        raw_bytes = raw_response.content
                        (root / raw_name).write_bytes(raw_bytes)
                        row.update(nasa_status=raw_response.status_code, raw_file=raw_name,
                                   sha256=hashlib.sha256(raw_bytes).hexdigest())
                        try:
                            row['source_unit'] = raw_response.json()['parameters'][variable]['units']
                        except (ValueError, KeyError, TypeError):
                            pass
                    rows.append(row)
                    (root / 'coverage.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
                    with (root / 'coverage.csv').open('w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=list(row))
                        writer.writeheader()
                        writer.writerows(rows)
                    print(json.dumps(row), flush=True)
                time.sleep(1)  # Sequential, modest request rate; no retry storm.
    print('Evidence: ' + str(root), flush=True)
    return 0 if len(rows) == 25 and all(r['success'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
