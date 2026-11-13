"""Only the indexed, reviewed controller sprite is a permitted binary asset."""
from pathlib import Path
import subprocess
import unittest

from tools.check_content import violations

ROOT = Path(__file__).resolve().parents[1]
ASSET = 'assets/controllers/ultimate2c-sprite.png'


class ControllerContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Match the checker: bytes come from the index, not a possibly edited
        # working copy. Never stage files or mutate the shared Git index.
        cls.data = subprocess.check_output(['git', 'show', ':' + ASSET], cwd=ROOT)

    def test_exact_reviewed_indexed_controller_is_allowed(self):
        self.assertEqual(violations(ASSET, self.data), [])

    def test_unreviewed_controller_content_paths_and_modes_stay_rejected(self):
        changed = bytearray(self.data)
        changed[-1] ^= 1
        for data in (bytes(changed), self.data + b'\0extra', self.data[:32], b'ordinary text'):
            with self.subTest(content_length=len(data)):
                self.assertTrue(violations(ASSET, data))
        for path in ('assets/controllers/unknown.png', 'assets/icons/ultimate2c-sprite.png',
                     'build/ultimate2c-sprite.png', 'assets/controllers/ultimate2c-sprite.exe'):
            with self.subTest(path=path):
                self.assertTrue(violations(path, self.data))
        for mode in ('120000', '160000', '100755'):
            with self.subTest(mode=mode):
                self.assertTrue(violations(ASSET, self.data, mode))
