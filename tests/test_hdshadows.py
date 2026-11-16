import unittest

import numpy as np

from newsnap import hdshadows as H


class Bc6hEncoder(unittest.TestCase):
    def test_round_trip_keeps_light_within_a_few_percent(self):
        y, x = np.mgrid[0:64, 0:64]
        img = np.stack([(x / 64) ** 2 * 3, np.sin(y / 9) + 1.2, (x * y / 4096) * 0.5 + 0.05], 2).astype(np.float32)
        img[20:30, 20:44] *= 0.2
        blob = H.encode_bc6h(img)
        self.assertEqual(len(blob), 64 * 64)   # one 16-byte block per 4x4 texels
        out = H.decode_bc6h(blob, 64, 64)
        self.assertLess(float((np.abs(out - img) / (img + 0.05)).mean()), 0.04)

    def test_flat_block_is_exact_enough(self):
        img = np.full((4, 4, 3), 0.75, np.float32)
        out = H.decode_bc6h(H.encode_bc6h(img), 4, 4)
        self.assertTrue(np.allclose(out, img, rtol=0.01))

    def test_anchor_index_has_no_top_bit(self):
        img = np.zeros((4, 4, 3), np.float32)
        img[0, 0] = 5.0   # the first texel at the bright end forces a swap of the endpoints
        blob = H.encode_bc6h(img)
        hi = int.from_bytes(blob[8:16], 'little')
        self.assertLess((hi >> 1) & 7, 8)
        self.assertTrue(np.allclose(H.decode_bc6h(blob, 4, 4)[0, 0], 5.0, rtol=0.02))


class LargeMaps(unittest.TestCase):
    def test_encoder_works_in_pieces_with_the_same_result(self):
        rng = np.random.default_rng(7)
        img = rng.random((4, 4 * 8200, 3), dtype=np.float32) * 4   # more blocks than one piece holds
        blob = H.encode_bc6h(img)
        self.assertEqual(len(blob), 8200 * 16)
        self.assertEqual(blob[-16 * 8:], H.encode_bc6h(np.ascontiguousarray(img[:, -32:])))
        self.assertEqual(blob[:16 * 8], H.encode_bc6h(np.ascontiguousarray(img[:, :32])))


class LightMaps(unittest.TestCase):
    def test_fill_reaches_empty_texels_and_keeps_islands(self):
        rgb = np.zeros((8, 8, 3), np.float32)
        rgb[2:4, 2:4] = 1.0
        mask = rgb.max(2) > 0
        filled = H.fill_empty(rgb, mask)
        self.assertTrue((filled[mask] == 1.0).all())
        self.assertTrue((filled[~mask] > 0).all())

    def test_directional_maps_are_left_alone(self):
        self.assertTrue(H.is_signed(np.full((4, 4, 3), -1.0, np.float32)))
        self.assertFalse(H.is_signed(np.ones((4, 4, 3), np.float32)))


if __name__ == '__main__':
    unittest.main()
