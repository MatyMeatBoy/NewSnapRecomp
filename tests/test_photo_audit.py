import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

import numpy as np
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

import audit_saved_photos as audit
from newsnap.saves import SAVE_NAMES, iv_mask

KEY = bytes(range(16))


def scene(size=(216, 144)):
    """Smooth bright gradient: no black rows unless a test paints them."""
    width, height = size
    x, y = np.meshgrid(np.linspace(60, 220, width), np.linspace(60, 200, height))
    return np.stack([x, y, (x + y) / 2], axis=2).astype(np.uint8)


def jpeg(pixels):
    out = io.BytesIO()
    Image.fromarray(pixels).save(out, 'JPEG', quality=92)
    return out.getvalue()


def bank(images, index, slots=4, damage=None):
    """Encrypted multi-slot container; `images` maps slot -> JPEG bytes."""
    decoded = (max(len(data) for data in images.values()) + 16 + 15) // 16 * 16
    packed = decoded + 48
    iv = bytes(range(16, 32))

    def encrypt(raw):
        return Cipher(algorithms.AES(KEY), modes.CBC(iv)).encryptor().update(raw)

    out = encrypt(struct.pack('<8I', 0xc63e569c, packed, decoded, slots, 48, 0, 0, 0))
    out += iv_mask(iv, 0xb519fc35 + index)
    for slot in range(slots):
        if slot not in images:
            out += bytes(packed)
            continue
        body = (bytes(16) + images[slot]).ljust(decoded, b'\0')
        stored = bytearray(body)
        if damage == slot:
            stored[200] ^= 0x55  # corrupt after checksums were computed
        entry = struct.pack('<8I', zlib.adler32(body), zlib.crc32(body), 0x9b7a0b7c,
                            decoded, decoded, 0, 0, 0) + bytes(stored)
        out += iv_mask(iv, 0xb519fc35 + index + slot) + encrypt(entry)
    return out


class BandDetectionTests(unittest.TestCase):
    def test_clean_picture_has_no_bands(self):
        bands = audit.black_bands(scene())
        self.assertEqual((bands['rows'], bands['columns'], bands['all_black']), ([], [], False))

    def test_interior_and_edge_bands_survive_jpeg(self):
        pixels = scene()
        pixels[48:64] = 0      # interior, MCU aligned
        pixels[-8:] = 0        # bottom edge
        pixels[:, 100:107] = 0  # interior column, unaligned
        report, decoded = audit.audit_jpeg(jpeg(pixels))
        self.assertEqual(decoded.shape, pixels.shape)
        rows = {(b['start'], b['length']): b for b in report['bands']['rows']}
        self.assertEqual(rows[(48, 16)]['kind'], 'interior')
        self.assertTrue(rows[(48, 16)]['aligned16'])
        self.assertEqual(rows[(136, 8)]['kind'], 'edge')
        column, = report['bands']['columns']
        self.assertEqual((column['kind'], column['aligned8']), ('interior', False))
        self.assertTrue(abs(column['start'] - 100) <= 1 and abs(column['length'] - 7) <= 2)
        self.assertTrue(audit.has_bands(report['bands'], interior_only=True))

    def test_partial_width_stripe_is_not_a_full_band_but_raises_black_fraction(self):
        pixels = scene()
        pixels[48:96, :108] = 0  # half-width tile, as in the owner's preview capture
        bands = audit.black_bands(pixels)
        self.assertEqual(bands['rows'], [])
        self.assertAlmostEqual(bands['black_fraction'], 48 * 108 / (216 * 144), places=3)
        self.assertTrue(bands['black_blocks_suspect'])
        self.assertTrue(audit.has_bands(bands))
        self.assertFalse(audit.has_bands(bands, interior_only=True))
        report, _ = audit.audit_jpeg(jpeg(pixels))
        self.assertTrue(report['bands']['black_blocks_suspect'])
        self.assertFalse(audit.black_bands(scene())['black_blocks_suspect'])

    def test_all_black_is_reported_separately(self):
        bands = audit.black_bands(np.zeros((16, 16, 3), np.uint8))
        self.assertTrue(bands['all_black'])
        self.assertFalse(audit.has_bands(bands))


class StructureTests(unittest.TestCase):
    def test_structure_reads_sof_and_flags_truncation(self):
        data = jpeg(scene())
        info = audit.jpeg_structure(data)
        self.assertEqual((info['width'], info['height'], info['sof'], info['problems']),
                         (216, 144, 'baseline', []))
        self.assertEqual(info['sampling'][0], '2x2')
        self.assertIn('sin EOI final', audit.jpeg_structure(data[:-2])['problems'])
        self.assertIn('sin SOI', audit.jpeg_structure(b'\0' + data)['problems'])

    def test_truncated_scan_is_a_decode_or_structure_problem(self):
        data = jpeg(scene())
        report, pixels = audit.audit_jpeg(data[:len(data) // 2])
        # A scan cut short must leave a trace: either Pillow refuses it or the
        # structure walk reports the missing end marker.
        self.assertTrue('decode_error' in report or 'sin EOI final' in report['structure']['problems'])


class BankAuditTests(unittest.TestCase):
    def write(self, folder, photos, thumbs, **kwargs):
        folder.mkdir(parents=True)
        (folder / SAVE_NAMES[3]).write_bytes(bank(photos, 3, **kwargs))
        (folder / SAVE_NAMES[4]).write_bytes(bank(thumbs, 4))

    def test_clean_bank_pairs_and_is_not_modified(self):
        with tempfile.TemporaryDirectory() as temporary:
            user = Path(temporary) / 'profile/save/user'
            pixels = scene((1080, 720))
            thumb = np.asarray(Image.fromarray(pixels[:, 108:972]).resize((240, 200), Image.Resampling.BOX))
            self.write(user, {1: jpeg(pixels)}, {1: jpeg(thumb)})
            before = (user / SAVE_NAMES[3]).read_bytes()
            report = audit.audit([Path(temporary) / 'profile'], KEY)
            self.assertEqual((user / SAVE_NAMES[3]).read_bytes(), before)
            self.assertTrue(all(b['unchanged_after_read'] and b['header']['size_ok'] for b in report['banks']))
            self.assertEqual(report['summary']['veredicto'], 'bytes-limpios')
            self.assertEqual(report['summary']['fotos']['dimensiones'], ['1080x720'])
            pair, = report['pairs']
            self.assertEqual(pair['slot'], 1)
            self.assertLess(pair['mean_abs_luma'], 3)
            json.dumps(report)  # report must stay serialisable and image-free

    def test_bands_in_photo_bytes_change_verdict_and_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pixels = scene()
            pixels[32:64] = 0
            self.write(root / 'user', {0: jpeg(pixels), 2: jpeg(scene())}, {0: jpeg(scene((48, 40)))})
            report = audit.audit([root / 'user'], KEY, root / 'flagged')
            self.assertEqual(report['summary']['veredicto'], 'bandas-en-bytes-de-foto')
            self.assertEqual(report['summary']['fotos']['con_bandas_interiores'], 1)
            self.assertEqual(len(list((root / 'flagged').iterdir())), 1)

    def test_bands_only_in_thumbnail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            thumb = scene((48, 40))
            thumb[8:24] = 0
            self.write(root / 'user', {0: jpeg(scene())}, {0: jpeg(thumb)})
            report = audit.audit([root / 'user'], KEY)
            self.assertEqual(report['summary']['veredicto'], 'bandas-solo-en-miniaturas-guardadas')
            self.assertGreater(report['pairs'][0]['worst_row_mean'], 50)

    def test_damaged_slot_is_reported_without_hiding_the_rest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write(root / 'user', {0: jpeg(scene()), 1: jpeg(scene())}, {0: jpeg(scene((48, 40)))}, damage=0)
            report = audit.audit([root / 'user' / SAVE_NAMES[3]], KEY)
            slots = {slot['slot']: slot for slot in report['banks'][0]['slots']}
            self.assertEqual(slots[0]['status'], 'foto-checksum-inválido')
            self.assertFalse(slots[0]['crc_ok'] or slots[0]['adler_ok'])
            self.assertEqual(slots[1]['status'], 'foto')
            self.assertEqual(report['summary']['fotos']['checksum_inválido'], 1)
            self.assertEqual(report['summary']['veredicto'], 'incompleto-o-dañado')

    def test_wrong_key_is_an_explicit_bank_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write(root / 'user', {0: jpeg(scene())}, {0: jpeg(scene((48, 40)))})
            report = audit.audit([root / 'user'], bytes(16))
            self.assertTrue(all('error' in b and b['unchanged_after_read'] for b in report['banks']))
            self.assertEqual(report['summary']['veredicto'], 'incompleto-o-dañado')
            self.assertFalse(report['summary']['evidencia_completa'])

    def test_cli_refuses_to_write_inside_save_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write(root / 'profile/save/user', {0: jpeg(scene())}, {0: jpeg(scene((48, 40)))})
            with patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                audit.main([str(root / 'profile'), '--out', str(root / 'profile/save/report.json')])
            self.assertFalse((root / 'profile/save/report.json').exists())
            with patch('newsnap.saves.local_save_key', return_value=KEY), patch('sys.stdout', io.StringIO()):
                self.assertEqual(audit.main([str(root / 'profile'), '--out', str(root / 'out/report.json')]), 0)
            self.assertEqual(json.loads((root / 'out/report.json').read_text(encoding='utf-8'))['summary']['veredicto'],
                             'bytes-limpios')


UNREADABLE = b'\xff\xd8\xff\xe0\x00\x10' + bytes(14) + b'\xff\xd9'
SHORT_SOF = b'\xff\xd8\xff\xc0\x00\x02\xff\xd9'
SHORT_DRI = b'\xff\xd8\xff\xdd\x00\x02\xff\xd9'


class ReviewRegressionTests(unittest.TestCase):
    """Reproductions from docs/bugs/photo-audit-review.md."""

    def bank_copy(self, root, images=None):
        # Deliberately not under a folder called save/save-tx/...: the guard
        # must not depend on protected folder names.
        folder = root / 'copia'
        folder.mkdir(parents=True)
        path = folder / SAVE_NAMES[3]
        path.write_bytes(bank(images or {0: jpeg(scene())}, 3))
        return path

    def run_main(self, arguments):
        with patch('newsnap.saves.local_save_key', return_value=KEY), \
                patch('sys.stdout', io.StringIO()), patch('sys.stderr', io.StringIO()):
            return audit.main([str(argument) for argument in arguments])

    def test_output_never_replaces_an_input_bank(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.bank_copy(root)
            original = path.read_bytes()
            for out in (path, path.parent / 'informe.json', path.parent / 'sub/informe.json'):
                with self.assertRaises(SystemExit):
                    self.run_main([path, '--out', out])
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(out.exists() and out != path)
            with self.assertRaises(SystemExit):  # also when the source is the folder
                self.run_main([path.parent, '--out', path])
            with self.assertRaises(SystemExit):  # bank-named output elsewhere
                self.run_main([path, '--out', root / 'otra' / SAVE_NAMES[4]])
            self.assertEqual(path.read_bytes(), original)

    def test_output_hardlinked_to_input_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.bank_copy(root)
            original = path.read_bytes()
            link = root / 'fuera' / 'informe.json'
            link.parent.mkdir()
            try:
                link.hardlink_to(path)
            except OSError:
                self.skipTest('el sistema de archivos no admite hardlinks')
            with self.assertRaises(SystemExit):
                self.run_main([path, '--out', link])
            self.assertEqual(path.read_bytes(), original)

    def test_export_folder_cannot_be_an_input_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pixels = scene()
            pixels[32:64] = 0
            path = self.bank_copy(root, {0: jpeg(pixels)})
            before = sorted(path.parent.iterdir())
            with self.assertRaises(SystemExit):
                self.run_main([path, '--out', root / 'out/informe.json', '--export-flagged', path.parent])
            with self.assertRaises(audit.UnsafeOutput):
                audit.audit([path], KEY, path.parent / 'flagged')
            self.assertEqual(sorted(path.parent.iterdir()), before)
            with self.assertRaises(SystemExit):  # report inside the export folder
                self.run_main([path, '--out', root / 'exp/informe.json', '--export-flagged', root / 'exp'])

    def test_malformed_segments_do_not_raise(self):
        for data, problem in ((SHORT_SOF, 'SOF demasiado corto'), (SHORT_DRI, 'DRI demasiado corto')):
            info = audit.jpeg_structure(data)
            self.assertTrue(any(problem in text for text in info['problems']), info)
            report, pixels = audit.audit_jpeg(data)
            self.assertIsNone(pixels)
            self.assertIn('decode_error', report)

    def test_malformed_entries_keep_the_rest_of_the_bank(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # FF D8 FF is required for an entry to count as a photograph.
            path = self.bank_copy(root, {0: SHORT_SOF, 1: SHORT_DRI, 2: jpeg(scene())})
            report = audit.audit([path], KEY)
            bank_report, = report['banks']
            self.assertNotIn('error', bank_report)
            slots = {slot['slot']: slot for slot in bank_report['slots']}
            self.assertEqual(set(slots), {0, 1, 2})
            self.assertIn('decode_error', slots[0]['jpeg'])
            self.assertIn('decode_error', slots[1]['jpeg'])
            self.assertEqual(slots[2]['jpeg']['bands']['rows'], [])
            self.assertEqual(report['summary']['veredicto'], 'incompleto-o-dañado')
            self.assertEqual(len(report['summary']['incidencias']), 2)

    def test_unreadable_jpeg_with_valid_checksum_is_not_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.bank_copy(root, {0: UNREADABLE})
            report = audit.audit([path], KEY)
            slot, = report['banks'][0]['slots']
            self.assertEqual(slot['status'], 'foto')  # container checksums are valid
            self.assertTrue(slot['crc_ok'] and slot['adler_ok'])
            summary = report['summary']
            self.assertEqual((summary['fotos']['decodificación_fallida'], summary['veredicto'],
                              summary['evidencia_completa']), (1, 'incompleto-o-dañado', False))
            self.assertEqual(self.run_main([path, '--out', root / 'out/informe.json']), 2)

    def test_exit_codes_distinguish_clean_and_banded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clean = self.bank_copy(root / 'a')
            pixels = scene()
            pixels[32:64] = 0
            banded = self.bank_copy(root / 'b', {0: jpeg(pixels)})
            self.assertEqual(self.run_main([clean, '--out', root / 'out/a.json']), 0)
            self.assertEqual(self.run_main([banded, '--out', root / 'out/b.json']), 1)

    def test_no_banks_found_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = audit.audit([Path(temporary)], KEY)
            self.assertEqual(report['summary']['veredicto'], 'incompleto-o-dañado')


if __name__ == '__main__':
    unittest.main()
