"""Source releases must exclude untracked private data and identify every byte."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import package_alpha


class AlphaPackageTests(unittest.TestCase):
    def test_source_archive_is_tracked_only_with_verified_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'README.md').write_text('original source')
            (root / 'prod.keys').write_text('private untracked fixture')
            (root / 'third_party/astral').mkdir(parents=True)
            (root / 'third_party/astral/LICENSE').write_text('upstream notice')
            def tracked(folder):
                return ['README.md'] if folder == root else ['LICENSE']
            with patch.object(package_alpha, 'ROOT', root), \
                 patch.object(package_alpha, 'tracked', tracked), \
                 patch.object(package_alpha.subprocess, 'run', return_value=type('Result', (), {'returncode': 0})()), \
                 patch.object(package_alpha.subprocess, 'check_output', return_value='a' * 40):
                directory, archive = package_alpha.package()
                with self.assertRaises(FileExistsError):
                    package_alpha.package()
            self.assertIn(f'{package_alpha.VERSION}-source', archive.name)
            self.assertFalse((directory / 'prod.keys').exists())
            manifest = json.loads((directory / 'MANIFEST.json').read_text())
            self.assertFalse(manifest['private_game_data'])
            self.assertEqual(set(manifest['files']), {'README.md', 'third_party/astral/LICENSE'})
            for name, record in manifest['files'].items():
                data = (directory / name).read_bytes()
                self.assertEqual(record, {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            with zipfile.ZipFile(archive) as zipped:
                self.assertIsNone(zipped.testzip())
                self.assertFalse(any('keys' in name for name in zipped.namelist()))

    def test_dirty_sources_are_rejected_before_creating_artifacts(self):
        with patch.object(package_alpha.subprocess, 'run', return_value=type('Result', (), {'returncode': 1})()):
            with self.assertRaisesRegex(ValueError, 'source changes'):
                package_alpha.package()


if __name__ == '__main__':
    unittest.main()
