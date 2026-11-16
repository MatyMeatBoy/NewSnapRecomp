import json
import os
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


class RepeatedPreparationTests(unittest.TestCase):
    """A game start with nothing new to prepare does not run the preparation again."""
    def setUp(self):
        from tests.test_verified_files import aged
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'runtime'
        self.folder.mkdir()
        aged(self.folder / 'newsnap.exe', b'runtime')
        aged(self.folder / 'ac_xlate.exe', b'translator')
        aged(self.folder / 'ac_xlate.id', b'translator identity')
        aged(self.folder / 'shader-programs.bin', b'ACSPRG\0\0' + struct.pack('<II', 1, 0))
        aged(self.folder / 'shader-answers.bin', b'ACSANS\0\0' + struct.pack('<II', 2, 221) + bytes(221))
        self.runs = 0

        def runtime(command, logfile, env):
            self.runs += 1
            self.assertEqual(command[1], '--prepare-shaders')
            (self.folder / 'shader-prepared.bin').write_bytes(b'ACSPRP\0\0' + struct.pack('<II', 1, 36) + bytes(72))
            (self.folder / 'shader-cache').mkdir(exist_ok=True)
            Path(logfile).parent.mkdir(parents=True, exist_ok=True)
            Path(logfile).write_text('2 variants, 0 translations failed, in 5 ms\n; 0 failed, 0 not in the shader cache\n',
                                     encoding='utf-8')
        for item in (patch('newsnap.shaders.run_logged', side_effect=runtime), patch('newsnap.shaders.ROOT', self.root),
                     patch.dict(os.environ, {'NEWSNAP_PREPARE_ALWAYS': ''})):
            item.start()
            self.addCleanup(item.stop)
        self.aged = aged

    def test_same_inputs_are_prepared_once(self):
        self.assertEqual(prepare_observed(self.folder), 2)
        self.assertEqual(self.runs, 1)
        receipt = json.loads((self.folder / 'newsnap-shader-preparation.json').read_text())
        self.assertEqual(receipt['inputs']['scope'], 'observed')
        self.assertEqual(set(receipt['inputs']['files']),
                         {'newsnap.exe', 'ac_xlate.exe', 'ac_xlate.id', 'shader-answers.bin', 'shader-programs.bin'})
        seeds = [(self.folder / name).stat().st_mtime_ns for name in ('seed-answers.bin', 'seed-programs.bin')]
        for _ in range(3):
            self.assertEqual(prepare_observed(self.folder), 2)
        self.assertEqual(self.runs, 1)
        self.assertEqual(seeds, [(self.folder / name).stat().st_mtime_ns
                                 for name in ('seed-answers.bin', 'seed-programs.bin')])   # nothing rewritten

    def test_anything_new_prepares_again(self):
        prepare_observed(self.folder)
        changes = (
            lambda: self.aged(self.folder / 'shader-answers.bin',          # the game recorded another variant
                              b'ACSANS\0\0' + struct.pack('<II', 2, 221) + bytes(442), seconds=90),
            lambda: self.aged(self.folder / 'newsnap.exe', b'RUNTIME', seconds=80),          # another runtime
            lambda: self.aged(self.folder / 'ac_xlate.id', b'another translator', seconds=70),
            lambda: (self.folder / 'shader-prepared.bin').write_bytes(b'damaged'),
            lambda: (self.folder / 'seed-programs.bin').unlink(),
            lambda: (self.folder / 'shader-cache').rmdir(),                                  # translated shaders removed
            lambda: (self.folder / 'shader-prepare-journal.bin').write_bytes(b'crash'),      # the driver crashed
        )
        for number, change in enumerate(changes, 2):
            change()
            self.assertEqual(prepare_observed(self.folder), 2)
            self.assertEqual(self.runs, number, number)
            (self.folder / 'shader-prepare-journal.bin').unlink(missing_ok=True)
        prepare_observed(self.folder)
        runs = self.runs
        self.assertEqual(prepare_observed(self.folder), 2)
        self.assertEqual(self.runs, runs)

    def test_rebuilt_runtime_that_asks_for_preparation_gets_it(self):
        prepare_observed(self.folder)
        (self.folder / 'newsnap-game.json').write_text(json.dumps({'shader_preparation_required': True}))
        prepare_observed(self.folder)
        self.assertEqual(self.runs, 2)
        (self.folder / 'newsnap-game.json').write_text(json.dumps({'shader_preparation_required': False}))
        prepare_observed(self.folder)
        self.assertEqual(self.runs, 2)

    def test_receipt_of_an_earlier_version_and_the_override_prepare_again(self):
        prepare_observed(self.folder)
        receipt = json.loads((self.folder / 'newsnap-shader-preparation.json').read_text())
        del receipt['inputs'], receipt['shader_cache']          # as written before this change
        (self.folder / 'newsnap-shader-preparation.json').write_text(json.dumps(receipt))
        prepare_observed(self.folder)
        self.assertEqual(self.runs, 2)
        with patch.dict(os.environ, {'NEWSNAP_PREPARE_ALWAYS': '1'}):
            prepare_observed(self.folder)
        self.assertEqual(self.runs, 3)

    def test_library_scope_follows_the_library_files(self):
        from newsnap.shaders import preparation_inputs
        libraries = self.root / 'libraries'
        libraries.mkdir()
        (libraries / 'manifest.json').write_text('{"members": []}')
        self.aged(libraries / '00000.nushdb', b'library')
        first = preparation_inputs(self.folder, True, libraries)
        self.assertEqual(first, preparation_inputs(self.folder, True, libraries))
        self.assertNotEqual(first, preparation_inputs(self.folder, False, libraries))
        self.aged(libraries / '00000.nushdb', b'LIBRARY', seconds=60)
        self.assertNotEqual(first, preparation_inputs(self.folder, True, libraries))

