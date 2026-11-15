import unittest

import numpy as np

from newsnap import texpack_gen as T


class Bc1Bc3(unittest.TestCase):
    def test_gradient_round_trip(self):
        y, x = np.mgrid[0:32, 0:32]
        img = np.stack([x * 8, y * 8, (x + y) * 4, np.full_like(x, 255)], 2).astype(np.uint8)
        blob = T.encode(img, False)
        self.assertEqual(len(blob), 32 * 32 // 2)   # BC1: 8 bytes per 4x4
        self.assertLess(float(np.abs(T.decode_bc1(blob, 32, 32).astype(int) - img[..., :3]).mean()), 8)

    def test_alpha_makes_bc3(self):
        img = np.zeros((8, 8, 4), np.uint8)
        img[..., 3] = 128
        self.assertEqual(len(T.encode(img, True)), 8 * 8)   # BC3: 16 bytes per 4x4

    def test_flat_block_decodes_its_colour(self):
        img = np.full((4, 4, 4), 200, np.uint8)
        dec = T.decode_bc1(T.encode(img, False), 4, 4)
        self.assertLess(int(np.abs(dec.astype(int) - 200).max()), 5)


if __name__ == '__main__':
    unittest.main()
