import tempfile
from pathlib import Path
from unittest import TestCase
from newsnap.launcher_settings import load_settings, save_settings


class SettingsFilenameTests(TestCase):
    def test_legacy_read_and_first_new_save_preserve_unknown_values_and_old_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / 'astralchain.ini'
            raw = b'\xef\xbb\xbf; owner comment\r\n[display]\r\nvk_present = fifo\r\nunknown = keep\r\n'
            legacy.write_bytes(raw)
            target = root / 'newsnap.ini'
            self.assertEqual(load_settings(target)['vk_present'], 'fifo')
            self.assertFalse(target.exists())
            save_settings(target, {'vk_present': 'mailbox'})
            self.assertEqual(legacy.read_bytes(), raw)
            self.assertIn(b'unknown = keep\r\n', target.read_bytes())
            self.assertTrue(target.read_bytes().startswith(b'\xef\xbb\xbf'))
            self.assertEqual(load_settings(target)['vk_present'], 'mailbox')

    def test_existing_new_config_does_not_fall_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'astralchain.ini').write_text('[display]\nvk_present = fifo\n')
            target = root / 'newsnap.ini'
            target.write_text('; deliberately empty\n')
            self.assertEqual(load_settings(target)['vk_present'], 'mailbox')
