import struct
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from newsnap.shaders import validate_recording, prepare_observed, _preparation_outputs
from newsnap.nushdb import program_record, shaders
from tests.test_nushdb import library


class RecordingTests(unittest.TestCase):
    def test_preparation_transaction_commits_success_and_rolls_back_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            record = folder / 'shader-prepared.bin'
            receipt = folder / 'newsnap-shader-preparation.json'
            record.write_bytes(b'old record')
            receipt.write_bytes(b'old receipt')
            with _preparation_outputs(folder):
                record.write_bytes(b'new record')
                receipt.write_bytes(b'new receipt')
            self.assertEqual(record.read_bytes(), b'new record')
            self.assertEqual(receipt.read_bytes(), b'new receipt')
            with self.assertRaisesRegex(ValueError, 'invalid output'):
                with _preparation_outputs(folder):
                    record.write_bytes(b'corrupt record')
                    receipt.write_bytes(b'incomplete receipt')
                    raise ValueError('invalid output')
            self.assertEqual(record.read_bytes(), b'new record')
            self.assertEqual(receipt.read_bytes(), b'new receipt')
            self.assertEqual(sorted(p.name for p in folder.iterdir()),
                             ['newsnap-shader-preparation.json', 'shader-prepared.bin'])

    def test_failed_prepare_restores_previous_valid_record_and_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'newsnap.exe').touch()
            (folder / 'ac_xlate.exe').touch()
            (folder / 'shader-programs.bin').write_bytes(b'ACSPRG\0\0' + struct.pack('<II', 1, 0))
            (folder / 'shader-answers.bin').write_bytes(b'ACSANS\0\0' + struct.pack('<II', 2, 221))
            prepared = folder / 'shader-prepared.bin'
            old = b'ACSPRP\0\0' + struct.pack('<II', 1, 36) + bytes(36)
            prepared.write_bytes(old)
            receipt = folder / 'newsnap-shader-preparation.json'
            receipt.write_bytes(b'{"previous":"valid"}\n')

            def fail(*args):
                self.assertFalse(prepared.exists(), 'old output must not count as a new success')
                prepared.write_bytes(b'partial failed output')
                raise ValueError('translator failed')

            with patch('newsnap.shaders.run_logged', side_effect=fail):
                with self.assertRaisesRegex(ValueError, 'translator failed'):
                    prepare_observed(folder)
            self.assertEqual(prepared.read_bytes(), old)
            self.assertEqual(receipt.read_bytes(), b'{"previous":"valid"}\n')

    def test_first_failed_prepare_removes_partial_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'newsnap.exe').touch()
            (folder / 'shader-programs.bin').write_bytes(b'ACSPRG\0\0' + struct.pack('<II', 1, 0))
            (folder / 'shader-answers.bin').write_bytes(b'ACSANS\0\0' + struct.pack('<II', 2, 221))
            prepared = folder / 'shader-prepared.bin'

            def fail(*args):
                prepared.write_bytes(b'partial failed output')
                raise ValueError('driver failed')

            with patch('newsnap.shaders.run_logged', side_effect=fail):
                with self.assertRaisesRegex(ValueError, 'driver failed'):
                    prepare_observed(folder)
            self.assertFalse(prepared.exists())

    def test_torn_recordings_are_rejected_before_appending_defaults(self):
        answers = b'ACSANS\0\0' + struct.pack('<II', 2, 221)
        programs = b'ACSPRG\0\0' + struct.pack('<II', 1, 0)
        row, = shaders(library())
        record = program_record(*row)
        validate_recording(answers + bytes(221), True)
        validate_recording(programs + record, False)
        for data, answer in ((answers + bytes(220), True), (programs + record[:-1], False),
                             (programs + record + b'\0', False)):
            with self.assertRaises(ValueError):
                validate_recording(data, answer)
