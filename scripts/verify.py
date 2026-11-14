"""Run the complete offline suite; never silently pass missing dependencies."""
import importlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    missing = []
    for name in ['fastapi', 'uvicorn', 'numpy', 'scipy', 'statsmodels.api', 'httpx', 'reportlab', 'dotenv']:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    if missing:
        print('Missing dependencies: ' + ', '.join(missing), file=sys.stderr)
        print('Run: python -m pip install -r requirements.txt', file=sys.stderr)
        return 2
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    allowed = 0 if os.getenv('RUN_LIVE_NASA') == '1' else 1
    unexpected = [(str(t), why) for t, why in result.skipped
                  if not (allowed and str(t).startswith('test_live_singapore '))]
    if unexpected:
        print('Unexpected skipped tests: ' + repr(unexpected), file=sys.stderr)
    return 0 if result.wasSuccessful() and not unexpected else 1

if __name__ == '__main__':
    raise SystemExit(main())
