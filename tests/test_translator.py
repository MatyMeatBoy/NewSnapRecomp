"""The delivered executable and recipe id must both match the public pin."""
import json
import hashlib
import shutil
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsnap import translator as translator
from newsnap import build as builder
from tools import package_build_kit as packager


class TranslatorEarlyGateTests(unittest.TestCase):
    def test_rebuild_rejects_old_sdk_before_owner_verification(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'profiles').mkdir()
            (root / 'profiles/snap-2.0.1.json').write_text('{}')
            data = root / 'build/extracted/updated'
            (data / 'romfs').mkdir(parents=True)
            (data / 'extraction-manifest.json').write_text('{}')
            (data / 'romfs/import-receipt.json').write_text('{}')
            with patch.object(builder, 'ROOT', root), patch.object(builder, 'verify_import', side_effect=AssertionError('owner verification reached')) as owner:
                with self.assertRaisesRegex(ValueError, 'translator'):
                    builder.build(root / 'old-sdk')
                owner.assert_not_called()

    def test_package_rejects_old_sdk_before_git_or_staging(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with patch.object(packager.subprocess, 'run', side_effect=AssertionError('git reached')) as git:
                with self.assertRaisesRegex(ValueError, 'translator'):
                    packager.package(root / 'old-sdk', root / 'output')
                git.assert_not_called()
                self.assertFalse((root / 'output').exists())


class TranslatorIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'bin'
        self.source.mkdir()
        self.payload = b'MZ public translator fixture'
        (self.source / 'ac_xlate.exe').write_bytes(self.payload)
        self.identity = 'a' * 64
        (self.source / 'ac_xlate.id').write_text(self.identity + '\n', encoding='ascii')
        self.pin = self.root / 'pin.json'
        self.pin.write_text(json.dumps(dict(format=1, platform='windows-x64', size=len(self.payload),
                                sha256=hashlib.sha256(self.payload).hexdigest(), identity=self.identity)))

    def verify(self):
        return translator.verify_translator(self.source, pin_path=self.pin)

    def test_exact_pair_and_copy_verify_independently(self):
        self.assertEqual(self.verify()['identity'], self.identity)
        out = self.root / 'output'
        translator.stage_translator(self.source, out, pin_path=self.pin)
        self.assertEqual(translator.verify_translator(out, pin_path=self.pin)['identity'], self.identity)
        self.assertEqual((out / 'ac_xlate.exe').read_bytes(), self.payload)

    def test_old_binary_with_correct_id_still_rejected(self):
        (self.source / 'ac_xlate.exe').write_bytes(b'X' * len(self.payload))
        with self.assertRaisesRegex(ValueError, 'executable differs'):
            self.verify()

    def test_legacy_missing_and_forged_ids_rejected(self):
        for data in (b'b' * 64, b'old-version', b'a' * 64 + b' arbitrary suffix'):
            with self.subTest(identity=data):
                (self.source / 'ac_xlate.id').write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'translator'):
                    self.verify()
        (self.source / 'ac_xlate.id').unlink()
        with self.assertRaisesRegex(ValueError, 'translator'):
            self.verify()

    def test_corrupted_copy_cannot_replace_previous_output(self):
        out = self.root / 'output'
        out.mkdir()
        (out / 'ac_xlate.exe').write_bytes(b'previous exe')
        (out / 'ac_xlate.id').write_bytes(b'previous identity')
        copy = shutil.copy2
        def corrupt(source, target):
            result = copy(source, target)
            if Path(target).name == 'ac_xlate.exe':
                Path(target).write_bytes(b'X' * len(self.payload))
            return result
        with patch.object(translator.shutil, 'copy2', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'executable differs'):
                translator.stage_translator(self.source, out, pin_path=self.pin)
        self.assertEqual((out / 'ac_xlate.exe').read_bytes(), b'previous exe')
        self.assertEqual((out / 'ac_xlate.id').read_bytes(), b'previous identity')
        self.assertFalse(list(out.glob('.translator-*')))

    def test_malformed_pin_rejected(self):
        self.pin.write_text('{"format":1,"platform":"windows-x64","size":true}')
        with self.assertRaisesRegex(ValueError, 'public pin'):
            self.verify()

    def test_real_native_aot_pair_matches_checked_in_pin(self):
        path = os.environ.get('NEWSNAP_XLATE_REAL_BIN')
        if not path:
            self.skipTest('set NEWSNAP_XLATE_REAL_BIN to verify actual NativeAOT output')
        self.assertEqual(translator.verify_translator(path)['identity'],
                         'b9ccfec46b187eee1f6c3c281ad7ce4574a4877f7b334286b080bf3ee270902e')


if __name__ == '__main__':
    unittest.main()
