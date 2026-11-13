import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from newsnap.saves import decode_moves, iv_mask, saved_jpegs
from newsnap.photos import scan_photos


def jpeg(size=(64, 32)):
    out = io.BytesIO()
    Image.new('RGB', size, '#eab54a').save(out, 'JPEG')
    return out.getvalue()


def save_bank(image, key=bytes(range(16)), index=3):
    body = bytes(16) + image
    body += bytes((-len(body)) % 16)
    header = struct.pack('<8I', 0xc63e569c, len(body) + 48, len(body), 1, 48, 0, 0, 0)
    entry = struct.pack('<8I', zlib.adler32(body), zlib.crc32(body), 0x9b7a0b7c,
                        len(body), len(body), 0, 0, 0) + body
    iv = bytes(range(16, 32))
    enc = lambda raw: Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor().update(raw)
    masked = iv_mask(iv, 0xb519fc35 + index)
    return enc(header) + masked + masked + enc(entry)


class PhotoTests(unittest.TestCase):
    def test_saved_thumbnail_is_not_a_second_photo_and_is_kept_if_original_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user = root / 'profile/save/user'
            user.mkdir(parents=True)
            original = user / '00c31e53dde3ac51'
            original.write_bytes(save_bank(jpeg()))
            (user / '4f342de95be7450e').write_bytes(save_bank(jpeg((16, 8)), index=4))
            with patch('newsnap.photos.local_save_key', return_value=bytes(range(16))):
                photos = scan_photos(root / 'profile', root / 'cache')
                self.assertEqual([(p.width, p.height) for p in photos], [(64, 32)])
                # Matching slots belong to each user independently.
                other = user.parent / 'another-user'
                other.mkdir()
                (other / '4f342de95be7450e').write_bytes(save_bank(jpeg((24, 12)), index=4))
                photos = scan_photos(root / 'profile', root / 'cache')
                self.assertEqual(sorted((p.width, p.height) for p in photos), [(24, 12), (64, 32)])
                original.unlink()
                photos = scan_photos(root / 'profile', root / 'cache')
                self.assertEqual(sorted((p.width, p.height) for p in photos), [(16, 8), (24, 12)])

    def test_gallery_refuses_to_write_cache_into_save(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            with self.assertRaises(ValueError):
                scan_photos(profile, profile / 'save/user')
            self.assertFalse((profile / 'save').exists())

    def test_move_wide_reader_rejects_wrong_instructions(self):
        raw = b''.join(struct.pack('<I', (0xd2800000 if i == 0 else 0xf2800000)
                                   | (i << 21) | ((i + 1) << 5) | 10) for i in range(4))
        self.assertEqual(decode_moves(raw, 0), sum((i + 1) << (16 * i) for i in range(4)))
        with self.assertRaises(ValueError):
            decode_moves(raw[:12], 0)
        with self.assertRaises(ValueError):
            decode_moves(bytes(16), 0)

    def test_encrypted_photo_is_validated_and_source_is_unchanged(self):
        image = jpeg()
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / '00c31e53dde3ac51'
            original = save_bank(image)
            source.write_bytes(original)
            self.assertEqual(list(saved_jpegs(source, 3, bytes(range(16)))), [(0, image)])
            self.assertEqual(source.read_bytes(), original)
            for bad in (original[:-1], original[:80] + b'\x01' + original[81:]):
                source.write_bytes(bad)
                with self.assertRaises(ValueError):
                    list(saved_jpegs(source, 3, bytes(range(16))))

    def test_gallery_deduplicates_save_and_exports_and_ignores_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'
            bank = profile / 'save/user/00c31e53dde3ac51'
            bank.parent.mkdir(parents=True)
            bank.write_bytes(save_bank(jpeg()))
            exports = profile / 'photos'
            exports.mkdir()
            (exports / 'photo.jpg').write_bytes(jpeg())
            research = profile / 'research'
            research.mkdir()
            Image.new('RGB', (200, 100)).save(research / 'screenshot.png')
            with patch('newsnap.photos.local_save_key', return_value=bytes(range(16))):
                photos = scan_photos(profile, root / 'cache')
            self.assertEqual(len(photos), 1)
            self.assertEqual((photos[0].width, photos[0].height), (64, 32))
            self.assertEqual(photos[0].path.read_bytes(), jpeg())
