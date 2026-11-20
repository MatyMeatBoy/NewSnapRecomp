import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from newsnap import home_state, maintenance


class RomfsVariants(unittest.TestCase):
    def fixture(self, root, image):
        data = root / 'GameData'
        (data / 'exefs').mkdir(parents=True)
        (data / 'romfs').mkdir()
        modules = {'main': b'main fixture', 'sdk': b'sdk fixture'}
        for name, contents in modules.items(): (data / 'exefs' / name).write_bytes(contents)
        (data / 'romfs/romfs.bin').write_bytes(image)
        digest = lambda b: hashlib.sha256(b).hexdigest()
        profile = {'exefs_sha256': {k: digest(v) for k,v in modules.items()},
                   'romfs_sha256': digest(b'original'),
                   'romfs_normalized': {'sha256': digest(b'normalized'), 'size': 10},
                   'verified_control': {'display_version':'2.0.1', 'save_size':512, 'journal_size':1024}}
        return data, profile, digest

    def test_supported_normalized_identity_is_accepted_and_receipted_truthfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data,profile,digest=self.fixture(root,b'normalized')
            with patch.object(home_state,'_profile',return_value=profile):
                result=home_state.verify(root)
                self.assertTrue(result['verified'])
                receipt=home_state._receipt(data,profile)
                self.assertEqual(receipt['image_sha256'],digest(b'normalized'))
                receipts=home_state.owner_receipts(data,profile)
                self.assertEqual(receipts.digest(data/'romfs/romfs.bin'),digest(b'normalized'))

    def test_unknown_bytes_are_not_accepted_by_a_format_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            data,profile,_=self.fixture(Path(temporary),b'changed')
            (data/'nup-import.json').write_text('{"format":"newsnap-nup-import-v1"}')
            with self.assertRaisesRegex(ValueError,'RomFS'):
                maintenance.verify_owner_inputs(data,profile)
