import io
import struct
import tempfile
import unittest
from pathlib import Path

from newsnap.importer import select_program, source_digest, validated_existing
from newsnap.upstream import extractor


class PackageTests(unittest.TestCase):
    def test_rejects_wrong_game_and_missing_update_metadata(self):
        header = bytes(0xC00)
        good = {'content_type': 0, 'title_id': '0100F4300BF2C000'}
        meta = {'content_type': 1, 'title_id': '0100F4300BF2C800'}
        self.assertEqual(select_program([(good, header), (meta, header)], update=True)[0], good)
        with self.assertRaises(ValueError):
            select_program([({'content_type': 0, 'title_id': '01007300020FA000'}, header)])
        with self.assertRaises(ValueError):
            select_program([(good, header)], update=True)
        with self.assertRaises(ValueError):
            select_program([(good, header), (good, header)])

    def test_rejects_truncated_and_escaping_partitions(self):
        e = extractor()
        with self.assertRaises(ValueError):
            e.container_entries(io.BytesIO(b'PFS0'), 4)
        name = b'../main\0'
        raw = b'PFS0' + struct.pack('<III', 1, len(name), 0)
        raw += struct.pack('<QQII', 0, 0, 0, 0) + name
        with self.assertRaises(ValueError):
            e.container_entries(io.BytesIO(raw), len(raw))

    def test_reuse_requires_source_and_output_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root / 'input.nsp', root / 'exefs'
            source.write_bytes(b'original')
            output.mkdir()
            (output / 'main').write_bytes(b'code')
            manifest = {'source_sha256': source_digest(source),
                        'files': [{'name': 'main', 'sha256': source_digest(output / 'main')}]}
            self.assertTrue(validated_existing(source, output, manifest))
            source.write_bytes(b'modified')
            self.assertFalse(validated_existing(source, output, manifest))
            source.write_bytes(b'original')
            (output / 'main').write_bytes(b'bad!')
            self.assertFalse(validated_existing(source, output, manifest))


if __name__ == '__main__':
    unittest.main()
