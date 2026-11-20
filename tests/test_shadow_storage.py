import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsnap import shadow_storage as S


class GeneratedCompression(unittest.TestCase):
    def test_non_windows_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(S, '_WINDOWS', False):
            folder = Path(tmp) / 'absent'
            self.assertFalse(S.enable_generated_compression(folder))
            self.assertFalse(folder.exists())

    def test_unsupported_filesystem_keeps_existing_bytes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(S, '_WINDOWS', True), \
                patch.object(S, '_compress_directory', side_effect=OSError('unsupported')):
            folder = Path(tmp)
            old = folder / 'old.dds'
            old.write_bytes(b'original compressed texture bytes')
            messages = []
            self.assertFalse(S.enable_generated_compression(folder, messages.append))
            self.assertEqual(old.read_bytes(), b'original compressed texture bytes')
            self.assertTrue(messages)

    def test_only_directory_is_configured(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(S, '_WINDOWS', True), \
                patch.object(S, '_compress_directory') as compress:
            folder = Path(tmp) / 'generated'
            self.assertTrue(S.enable_generated_compression(folder))
            compress.assert_called_once_with(folder.absolute())

    def test_reparse_parent_is_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(S, '_WINDOWS', True), \
                patch.object(S, '_is_reparse', side_effect=lambda p: p == Path(tmp)), \
                patch.object(S, '_compress_directory') as compress:
            folder = Path(tmp) / 'generated'
            self.assertFalse(S.enable_generated_compression(folder, lambda _: None))
            self.assertFalse(folder.exists())
            compress.assert_not_called()

    @unittest.skipUnless(os.name == 'nt', 'Windows filesystem integration')
    def test_windows_new_part_inherits_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'generated'
            if not S.enable_generated_compression(folder, lambda _: None):
                self.skipTest('compression unavailable on temporary filesystem')
            data = bytes(range(256)) * 4096
            target = folder / 'fixture.part'
            target.write_bytes(data)
            target = target.rename(folder / 'fixture.dds')
            self.assertEqual(target.read_bytes(), data)
            self.assertTrue(target.stat().st_file_attributes & 0x800)
