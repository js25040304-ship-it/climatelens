"""Package real archived NASA evidence for the static shared preview.

The normal FastAPI deployment remains live. No synthetic fallback is created.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.data import CITIES, VARIABLES
ARCHIVE = ROOT / 'evidence/nasa-data/20261114T080209845385Z'

def build(destination):
    destination = Path(destination).resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name != 'dist':
        raise ValueError('Use a separate directory named dist inside the repository, or an external directory.')
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'app/static', destination / 'static', dirs_exist_ok=True)
    html = (ROOT / 'app/static/index.html').read_text(encoding='utf-8-sig')
    html = html.replace('<body>', '<body data-mode="snapshot">')
    html = html.replace('<script src="/static/ui-utils.js"', '<script src="/static/snapshot-preview.js" defer></script><script src="/static/ui-utils.js"')
    (destination / 'index.html').write_text(html, encoding='utf-8')
    records = {}
    for file in sorted((ARCHIVE / 'results').glob('*.json')):
        result = json.loads(file.read_text(encoding='utf-8'))
        s = result['settings']
        raw = ARCHIVE / 'raw' / file.name
        if not raw.is_file() or not result.get('stats') or len(result['annual']) != 25:
            raise ValueError(f'Incomplete archive: {file.name}')
        result['id'] = 'snapshot:' + file.stem
        result['archive_provenance'] = {'path': file.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
            'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest()}
        records[f"{s['city']}|{s['variable']}"] = result
    if len(records) != len(CITIES) * len(VARIABLES):
        raise ValueError('Expected one archive for every city and variable.')
    bundle = {'catalog': {'cities': CITIES, 'variables': VARIABLES}, 'records': records,
              'archive': '20261114T080209845385Z', 'period': [2001, 2025],
              'notice': 'Saved real NASA responses and recorded server analysis. Not a live request.'}
    (destination / 'static/recorded-evidence.json').write_text(json.dumps(bundle, ensure_ascii=False), encoding='utf-8')
    print(f'Packaged {len(records)} real NASA records into {destination}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    build(parser.parse_args().destination)
