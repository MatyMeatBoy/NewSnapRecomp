import json
import struct
import tempfile
import unittest
from pathlib import Path

from newsnap.provenance import generation_recipe, record_generation, verify_generation, verify_import
from newsnap.importer import write_json, source_digest, read_control_metadata


def control_fixture(folder):
    folder.mkdir(parents=True, exist_ok=True)
    data = bytearray(256 + 0x4000)
    struct.pack_into('<10Q', data, 0, 80, 80, 0, 80, 24, 104, 0, 104, 44, 256)
    struct.pack_into('<6I', data, 80, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0, 0xFFFFFFFF, 0)
    struct.pack_into('<IIQQII', data, 104, 0, 0xFFFFFFFF, 0, 0x4000, 0xFFFFFFFF, 12)
    data[136:148] = b'control.nacp'
    data[256 + 0x3060:256 + 0x3065] = b'1.2.3'
    struct.pack_into('<QQ', data, 256 + 0x3080, 1024, 512)
    (folder / 'romfs.bin').write_bytes(data)
    write_json(folder / 'receipt.json', {'source_sha256': 'updated', 'romfs_sha256': source_digest(folder / 'romfs.bin')})


class ProvenanceTests(unittest.TestCase):
    def test_changed_instruction_patch_invalidates_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'recomp').mkdir()
            (root / 'tools').mkdir()
            (root / 'recomp/gen.py').write_text('# synthetic generator')
            patch = root / 'snap.txt'
            patch.write_text('original verified patch')
            generated = root / 'generated'
            generated.mkdir()
            (generated / 'layout.json').write_text('[]')
            recipe = generation_recipe(root, {'files': []}, patch)
            record_generation(generated, recipe)
            verify_generation(generated, recipe)
            patch.write_text('different patch at the same path')
            with self.assertRaises(ValueError):
                verify_generation(generated, generation_recipe(root, {'files': []}, patch))

    def test_modified_metadata_is_rederived_from_verified_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            control_fixture(folder)
            write_json(folder / 'metadata.json', {'save_size': 'C token', 'journal_size': -1})
            result = read_control_metadata(folder)
            self.assertEqual(result, {'display_version': '1.2.3', 'save_size': 1024, 'journal_size': 512})
            (folder / 'romfs.bin').write_bytes(b'corruption')
            with self.assertRaises(ValueError):
                read_control_metadata(folder)

    def test_build_validation_rejects_modified_index_and_modules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = root / 'updated'
            (updated / 'exefs').mkdir(parents=True)
            (updated / 'romfs').mkdir()
            (updated / 'exefs/main').write_bytes(b'synthetic module')
            (updated / 'romfs/romfs.bin').write_bytes(b'synthetic image')
            (updated / 'romfs/index.json').write_text('[]')
            for tag in ('base', 'updated'):
                write_json(root / tag / 'extraction-manifest.json', {
                    'source_sha256': tag,
                    'files': [{'name': 'main', 'sha256': source_digest(updated / 'exefs/main')}]})
            write_json(updated / 'romfs/import-receipt.json', {
                'sources': {'base': 'base', 'updated': 'updated'},
                'romfs_sha256': source_digest(updated / 'romfs/romfs.bin'),
                'index_sha256': source_digest(updated / 'romfs/index.json')})
            control_fixture(updated / 'control')
            verify_import(updated)
            (updated / 'romfs/index.json').write_text('["changed path"]')
            with self.assertRaises(ValueError):
                verify_import(updated)
            (updated / 'romfs/index.json').write_text('[]')
            (updated / 'exefs/main').write_bytes(b'changed module')
            with self.assertRaises(ValueError):
                verify_import(updated)

    def test_rejects_stale_and_modified_generated_code(self):
        with tempfile.TemporaryDirectory() as folder:
            generated = Path(folder)
            (generated / 'layout.json').write_text('[]')
            (generated / 'main.c').write_text('old instructions')
            recipe = {'main': 'input hash', 'lifter': 'lifter hash'}
            record_generation(generated, recipe)
            verify_generation(generated, recipe)
            with self.assertRaises(ValueError):
                verify_generation(generated, dict(recipe, main='new input hash'))
            (generated / 'main.c').write_text('different instructions')
            with self.assertRaises(ValueError):
                verify_generation(generated, recipe)


if __name__ == '__main__':
    unittest.main()
