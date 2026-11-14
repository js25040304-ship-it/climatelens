"""Exercise an actually running HTTP server without contacting external services."""
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE = 'http://127.0.0.1:8000'
for attempt in range(30):
    try:
        with urlopen(BASE + '/api/health', timeout=2) as response:
            assert json.load(response)['status'] == 'ok'
        break
    except URLError:
        time.sleep(0.5)
else:
    raise RuntimeError('Server did not become ready')

for path, marker in [('/', b'ClimateLens'), ('/static/app.js', b'investigate'), ('/openapi.json', b'/api/report')]:
    with urlopen(BASE + path, timeout=5) as response:
        assert marker in response.read(), path

with urlopen(Request(BASE + '/api/report', data=b'{"conclusion":"Incomplete evidence smoke test"}',
                     headers={'Content-Type': 'application/json'}), timeout=15) as response:
    assert response.headers['content-type'] == 'application/pdf'
    assert response.read().startswith(b'%PDF-')
print('HTTP startup, page, static script, API schema and incomplete PDF checks passed.')
