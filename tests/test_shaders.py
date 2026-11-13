import struct
import unittest

from newsnap.shaders import validate_recording
from newsnap.nushdb import program_record, shaders
from tests.test_nushdb import library


class RecordingTests(unittest.TestCase):
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
