import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import fetch_dlss as dlss


class DlssProvisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'cache'
        self.runtime = Path(self.temp.name) / 'runtime'
        self.data = {dlss.DLL: b'MZ vendor fixture', dlss.FG_DLL: b'MZ frame generation fixture',
                     'LICENSE.txt': b'full vendor terms\n'}
        identities = {n: (len(b), hashlib.sha256(b).hexdigest()) for n, b in self.data.items()}
        self.patch = patch.object(dlss, 'FILES', identities)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def opener(self, url, timeout):
        self.assertTrue(url.startswith(dlss.BASE))
        self.assertEqual(timeout, 90)
        return io.BytesIO(self.data[url[len(dlss.BASE):]])

    def test_fetch_pins_bytes_and_install_keeps_license_and_receipt(self):
        dlss.fetch(self.root, self.opener)
        installed = dlss.install(self.root, self.runtime)
        self.assertEqual(installed.read_bytes(), self.data[dlss.DLL])
        self.assertEqual((self.runtime / 'licenses/NVIDIA-DLSS.txt').read_bytes(), self.data['LICENSE.txt'])
        receipt = json.loads((self.runtime / 'licenses/NVIDIA-DLSS-receipt.json').read_text())
        self.assertEqual(receipt['commit'], dlss.COMMIT)
        self.assertEqual(receipt['version'], dlss.VERSION)
        self.assertEqual((self.runtime / 'nvngx_dlssg.dll').read_bytes(), self.data[dlss.FG_DLL])
        self.assertEqual(sorted(self.runtime.glob('*.dll')), [installed, self.runtime / 'nvngx_dlssg.dll'])

    def test_verified_cache_does_not_download_again(self):
        dlss.fetch(self.root, self.opener)
        def offline(*args, **kwargs):
            raise AssertionError('verified cache must work offline')
        dlss.fetch(self.root, offline)
        self.assertTrue(dlss.verify(self.root))

    def test_bad_download_does_not_replace_existing_file(self):
        target = self.root / dlss.DLL
        target.parent.mkdir(parents=True)
        target.write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            dlss.fetch(self.root, lambda *a, **k: io.BytesIO(b'wrong model'))
        self.assertEqual(target.read_bytes(), b'existing')
        self.assertFalse((self.root / 'sdk-receipt.json').exists())

    def test_corrupt_license_prevents_any_install(self):
        dlss.fetch(self.root, self.opener)
        (self.root / 'LICENSE.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            dlss.install(self.root, self.runtime)
        self.assertFalse(self.runtime.exists())

    def test_missing_dll_and_same_size_tampering_are_rejected(self):
        self.assertFalse(dlss.verify(self.root))
        dlss.fetch(self.root, self.opener)
        target = self.root / dlss.DLL
        target.write_bytes(b'X' * len(self.data[dlss.DLL]))
        self.assertFalse(dlss.verify(self.root))
        with self.assertRaises(ValueError):
            dlss.install(self.root, self.runtime)


if __name__ == '__main__':
    unittest.main()
