import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

from newsnap import game_textures as G
from newsnap import hdshadows as H


def archive(members):
    """An unencrypted DRPF archive with the given (name, extension CRC, bytes) members."""
    table = bytes(range(128))
    count = struct.pack('<I', len(members))
    out = struct.pack('<5I', 0x7F0E5359, zlib.crc32(count + table), 0xC65753E8, 0x90, len(members)) + table
    for name, extension, data in members:
        text = name.encode('ascii') + b'\0'
        text += b'\0' * (-len(text) % 4)
        body = data + b'\0' * (-len(data) % 4)
        total = 24 + len(text) + len(body)
        out += struct.pack('<6I', zlib.crc32(data), 0xE0A331B4, total, extension, len(data), len(data)) + text + body
    return out


def index(files):
    rows, strings = b'', b''
    for path, offset, size in files:
        name = path.encode() + b'\0'
        rows += struct.pack('<QQII', offset, size, len(strings), len(name))
        strings += name
    return struct.pack('<8sQQ', b'ACRFS1', len(files), 24 + len(rows)) + rows + strings


LIGHT = 'LV_ENV_001_1_A^SM_ENV_001_1_Ground^42^groundShape1^0^0^Lightmap.nutexb'
SHADOW = 'LV_ENV_001_1_A^SM_ENV_001_1_Ground^42^groundShape1^0^Shadow.nutexb'


class Names(unittest.TestCase):
    def test_the_two_name_rules_are_the_list(self):
        self.assertEqual(G.kind_of(LIGHT), G.LIGHT)
        self.assertEqual(G.kind_of(SHADOW), G.SHADOW)
        # directional terms of the lighting and ordinary textures are not shadows
        self.assertEqual(G.kind_of(LIGHT.replace('^0^Lightmap', '^2^Lightmap')), 0)
        self.assertEqual(G.kind_of('SM_ENV_001_1_Ground_dif.nutexb'), 0)
        self.assertEqual(G.kind_of('pm0025_00_Shadow.nutexb'), 0)


class GameFiles(unittest.TestCase):
    def setUp(self):
        level = archive([(LIGHT, 0x5C156DBC, b'L' * 40), (SHADOW, 0x5C156DBC, b'S' * 24),
                         ('rock_dif.nutexb', 0x5C156DBC, b'D' * 8), (SHADOW, 0x2F6D9B0B, b'x' * 8)])
        other = archive([(SHADOW, 0x5C156DBC, b'S' * 24)])
        self.image = b'\0' * 64 + level + other
        self.files = [('nx/Pack/LevelComposite/master/LC_001_A.drp', 64, len(level)),
                      ('nx/Pack/Model/master/pm0001.drp', 64 + len(level), len(other)), ('readme.txt', 0, 4)]

    def test_index_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'romfs-index.bin'
            path.write_bytes(index(self.files))
            self.assertEqual(G.romfs_files(path), self.files)
            path.write_bytes(index(self.files)[:-3])
            with self.assertRaises(ValueError):
                G.romfs_files(path)
            path.write_bytes(b'nothing')
            with self.assertRaises(ValueError):
                G.romfs_files(path)

    def test_only_level_archives_and_texture_members(self):
        found = G.shadow_members(io.BytesIO(self.image), self.files)
        self.assertEqual(list(found), ['nx/Pack/LevelComposite/master/LC_001_A.drp'])
        self.assertEqual([(m['name'], m['kind']) for m in found[self.files[0][0]]], [(LIGHT, 1), (SHADOW, 2)])

    def test_request_is_version_2_with_a_kind_per_member(self):
        stream = io.BytesIO(self.image)
        members = G.shadow_members(stream, self.files)[self.files[0][0]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'request.bin'
            G.write_request(stream, members, path)
            data = path.read_bytes()
        self.assertEqual(struct.unpack_from('<3I', data), (0x444F534E, 2, 2))
        first = struct.unpack_from('<6I', data, 12)
        self.assertEqual(first, (0, 40, 40, zlib.crc32(b'L' * 40), 0, 1))
        self.assertEqual(data[36:76], b'L' * 40)
        self.assertEqual(struct.unpack_from('<6I', data, 76), (1, 24, 24, zlib.crc32(b'S' * 24), 0, 2))
        self.assertEqual(len(data), 76 + 24 + 24)


class State(unittest.TestCase):
    def test_marker_belongs_to_this_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertFalse(G.complete(folder))
            (folder / G.MARKER).write_text(json.dumps({'build': G.BUILD, 'textures': 3}))
            self.assertTrue(G.complete(folder))
            (folder / G.MARKER).write_text(json.dumps({'build': G.BUILD + 1}))
            self.assertFalse(G.complete(folder))
            (folder / G.MARKER).write_text('[]')
            self.assertFalse(G.complete(folder))

    def test_built_means_an_hd_file_or_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertFalse(G._built(folder, ''))
            self.assertTrue(G._built(folder, '-'))
            self.assertFalse(G._built(folder, '0123456789abcdef'))
            (folder / '0123456789abcdef.skip').write_bytes(b'')
            self.assertTrue(G._built(folder, '0123456789abcdef'))


def plain_upscale(folder_in, folder_out, scale, model=None):
    Path(folder_out).mkdir(parents=True, exist_ok=True)
    for picture in Path(folder_in).glob('*.png'):
        with Image.open(picture) as im:
            im.resize((im.width * scale, im.height * scale), Image.BICUBIC).save(Path(folder_out) / picture.name)


def write_light(path, rgb):
    h, w, _ = rgb.shape
    px = np.concatenate([rgb, np.ones((h, w, 1), np.float32)], axis=2).astype(np.float16)
    header = bytearray(148)
    header[:4] = b'DDS '
    struct.pack_into('<II', header, 12, h, w)
    header[84:88] = b'DX10'
    struct.pack_into('<I', header, 128, 10)
    Path(path).write_bytes(bytes(header) + px.tobytes())


class Masks(unittest.TestCase):
    def test_bc3_alpha_round_trip(self):
        y, x = np.mgrid[0:32, 0:32]
        alpha = np.clip((x - y) * 20 + 128, 0, 255).astype(np.uint8)
        blob = H.encode_mask(alpha)
        self.assertEqual(len(blob), 8 * 8 * 16)
        self.assertFalse(np.frombuffer(blob, '<u8').reshape(-1, 2)[:, 1].any())   # black colour, as the game's
        out = H.decode_mask(blob, 32, 32)
        self.assertLessEqual(int(np.abs(out.astype(int) - alpha).max()), 20)
        flat = np.full((8, 8), 255, np.uint8)
        self.assertTrue((H.decode_mask(H.encode_mask(flat), 8, 8) == 255).all())
        self.assertTrue((H.decode_mask(H.encode_mask(flat * 0), 8, 8) == 0).all())


class Generate(unittest.TestCase):
    def setUp(self):
        self.real = H.upscale
        H.upscale = plain_upscale

    def tearDown(self):
        H.upscale = self.real

    def test_light_maps_and_masks_in_one_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'src').mkdir()
            y, x = np.mgrid[0:64, 0:64]
            write_light(folder / 'src/00000000000000aa.dds', np.stack([x / 64, y / 64, x * 0 + 0.5], 2).astype(np.float32))
            write_light(folder / 'src/00000000000000ab.dds', np.full((64, 64, 3), -0.5, np.float32))   # directional
            mask = np.zeros((64, 64, 4), np.uint8)
            mask[16:48, 16:48, 3] = 255
            Image.fromarray(mask, 'RGBA').save(folder / 'src/00000000000000ba.png')
            Image.fromarray(mask * 0, 'RGBA').save(folder / 'src/00000000000000bb.png')              # empty mask
            coloured = mask.copy()
            coloured[..., 0] = 90
            Image.fromarray(coloured, 'RGBA').save(folder / 'src/00000000000000bc.png')              # not a mask
            self.assertEqual(len(H.pending(folder)), 5)
            seen = []
            made, kept, failed = H.generate(folder, 2, report=lambda text: None, progress=lambda n, t: seen.append((n, t)))
            self.assertEqual((made, kept, failed), (2, 3, 0))
            self.assertEqual(seen, [(5, 5)])
            self.assertEqual(H.pending(folder), [])
            for name in ('ab', 'bb', 'bc'):
                self.assertTrue((folder / f'00000000000000{name}.skip').is_file())
            light = (folder / '00000000000000aa.dds').read_bytes()
            self.assertEqual(struct.unpack_from('<II', light, 12), (128, 128))
            self.assertEqual(struct.unpack_from('<I', light, 128)[0], 95)       # BC6H_UF16
            shadow = (folder / '00000000000000ba.dds').read_bytes()
            self.assertEqual(struct.unpack_from('<II', shadow, 12), (128, 128))
            self.assertEqual(struct.unpack_from('<I', shadow, 128)[0], 78)      # BC3 sRGB
            levels = struct.unpack_from('<I', shadow, 28)[0]
            self.assertEqual(len(shadow), 148 + sum(max(1, 32 >> l) ** 2 * 16 for l in range(levels)))
            alpha = H.decode_mask(shadow[148:148 + 32 * 32 * 16], 128, 128)
            self.assertTrue((alpha[40:88, 40:88] == 255).all())                 # the shadow stays where it was
            self.assertTrue((alpha[:24] == 0).all() and (alpha[:, 104:] == 0).all())

    def test_the_largest_light_maps_are_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'src').mkdir()
            write_light(folder / 'src/00000000000000da.dds', np.full((8, H.LIGHT_EDGE, 3), 0.5, np.float32))
            self.assertEqual(H.generate(folder, 2, report=lambda text: None), (0, 1, 0))
            self.assertTrue((folder / '00000000000000da.skip').is_file())

    def test_the_largest_masks_are_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'src').mkdir()
            mask = np.zeros((H.MASK_EDGE, 64, 4), np.uint8)
            mask[:100, :, 3] = 255
            Image.fromarray(mask, 'RGBA').save(folder / 'src/00000000000000ca.png')
            self.assertEqual(H.generate(folder, 2, report=lambda text: None), (0, 1, 0))


if __name__ == '__main__':
    unittest.main()
