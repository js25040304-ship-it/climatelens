"""The shared preview must preserve the real evidence rather than invent values."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.build_shared_preview import build, ROOT, ARCHIVE

class SharedPreviewTests(unittest.TestCase):
    def test_all_saved_observations_and_statistics_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            build(folder)
            bundle = json.loads((Path(folder) / 'static/recorded-evidence.json').read_text(encoding='utf-8'))
            self.assertEqual(len(bundle['records']), 25)
            for source in (ARCHIVE / 'results').glob('*.json'):
                original = json.loads(source.read_text(encoding='utf-8'))
                s = original['settings']
                saved = bundle['records'][f"{s['city']}|{s['variable']}"]
                for field in ['settings', 'annual', 'stats', 'source_url', 'retrieved_at', 'excluded_years']:
                    self.assertEqual(saved[field], original[field], (source.name, field))
                self.assertTrue(saved['id'].startswith('snapshot:'))
                self.assertEqual(len(saved['archive_provenance']['raw_sha256']), 64)

    def test_live_app_does_not_load_the_archive_adapter(self):
        live = (ROOT / 'app/static/index.html').read_text(encoding='utf-8-sig')
        self.assertNotIn('snapshot-preview.js', live)
        self.assertNotIn('data-mode="snapshot"', live)
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            build(folder)
            preview = (Path(folder) / 'index.html').read_text(encoding='utf-8')
            self.assertIn('data-mode="snapshot"', preview)
            self.assertIn('/static/snapshot-preview.js', preview)
            self.assertFalse((Path(folder) / '.env').exists())
