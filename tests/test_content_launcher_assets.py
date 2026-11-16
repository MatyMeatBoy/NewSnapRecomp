"""Only exact reviewed promotional images may enter the index."""
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.check_content import violations

ROOT=Path(__file__).resolve().parents[1]
ASSETS=('assets/launcher/lental-hero.jpg','assets/launcher/lental-explore.jpg',
        'assets/launcher/snap-logo.png',
        'docs/showcase/overview.png', 'docs/showcase/comparison.png')


class LauncherAssetContentTests(unittest.TestCase):
    def test_exact_reviewed_images_are_allowed(self):
        for name in ASSETS:
            with self.subTest(path=name):
                self.assertEqual(violations(name,(ROOT/name).read_bytes(),'100644'),[])

    def test_corruption_truncation_text_and_wrong_header_stay_rejected(self):
        for name in ASSETS:
            data=(ROOT/name).read_bytes()
            changed=bytearray(data);changed[-1]^=1
            bad_header=bytearray(data);bad_header[0]^=1
            for candidate in (bytes(changed),bytes(bad_header),data[:-1],data+b'\0extra',b'ordinary text'):
                with self.subTest(path=name,length=len(candidate)):
                    self.assertTrue(violations(name,candidate))

    def test_renamed_files_swapped_assets_and_wrong_modes_stay_rejected(self):
        for index,name in enumerate(ASSETS):
            data=(ROOT/name).read_bytes()
            for path in ('assets/launcher/renamed-'+Path(name).name,
                         'assets/icons/'+Path(name).name,'build/'+Path(name).name,
                         ASSETS[(index+1)%len(ASSETS)]):
                with self.subTest(path=path):self.assertTrue(violations(path,data))
            for mode in ('100755','120000','160000'):
                with self.subTest(path=name,mode=mode):self.assertTrue(violations(name,data,mode))

    def test_unknown_jpeg_png_are_rejected_even_without_nul_bytes(self):
        for path,data in (('assets/launcher/unknown.jpg',b'\xff\xd8\xff\xd9'),
                          ('assets/launcher/unknown.jpeg',b'\xff\xd8\xff\xd9'),
                          ('assets/launcher/unknown.PNG',b'\x89PNG\r\n\x1a\n'),
                          ('assets/launcher/unknown.png',b'not an approved image')):
            with self.subTest(path=path):self.assertTrue(violations(path,data))

    def test_acceptance_does_not_consult_mutable_provenance_metadata(self):
        name=ASSETS[0];data=(ROOT/name).read_bytes()
        # A changed source-pins.json cannot grant permission to changed bytes.
        # Content decisions use only the indexed path/mode/data and fixed code pins.
        with patch('builtins.open',side_effect=AssertionError('guard must not read mutable pins')):
            self.assertEqual(violations(name,data),[])
            self.assertTrue(violations(name,data+b'unreviewed'))
