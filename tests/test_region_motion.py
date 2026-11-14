import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

import measure_region_motion as motion

WIDTH, HEIGHT = 200, 120
BACKGROUND, SUBJECT = (10, 20, 90, 100), (120, 30, 180, 90)


def texture(seed, size):
    """Smooth random texture with gradients in every direction."""
    rng = np.random.default_rng(seed)
    coarse = rng.uniform(40, 215, size=(size[1] // 6 + 3, size[0] // 6 + 3))
    image = Image.fromarray(coarse.astype(np.uint8)).resize(size, Image.Resampling.BICUBIC)
    return np.asarray(image).astype(np.float64)


def frames(folder, background_steps, subject_steps):
    """Background and subject translate independently; frame k holds the summed steps."""
    base, subject = texture(1, (WIDTH + 80, HEIGHT + 40)), texture(2, (140, 140))
    bx = sx = 0.0
    for index in range(len(background_steps) + 1):
        picture = motion.shift(base, 20 - bx, 10)[:HEIGHT, :WIDTH].copy()
        patch_ = motion.shift(subject, 30 - sx, 30)
        x0, y0, x1, y1 = 112, 22, 188, 98
        picture[y0:y1, x0:x1] = patch_[y0 - 22:y1 - 22, x0 - 112:x1 - 112]
        Image.fromarray(np.clip(picture, 0, 255).astype(np.uint8)).save(folder / f'f{index + 100:06d}.png')
        if index < len(background_steps):
            bx += background_steps[index]
            sx += subject_steps[index]


class DisplacementTests(unittest.TestCase):
    def test_recovers_sub_pixel_translation(self):
        base = texture(3, (160, 120))
        for dx, dy in ((0.0, 0.0), (0.35, 0.0), (-1.2, 0.6), (2.4, -1.7)):
            moved = motion.shift(base, -dx, -dy)
            got_dx, got_dy, residual = motion.displacement(base, moved, (40, 30, 120, 90))
            self.assertAlmostEqual(got_dx, dx, delta=0.05)
            self.assertAlmostEqual(got_dy, dy, delta=0.05)
            self.assertLess(residual, 3.0)   # interpolation error only; changed content is above 15

    def test_changed_content_is_flagged_by_the_residual(self):
        _, _, residual = motion.displacement(texture(4, (160, 120)), texture(5, (160, 120)), (40, 30, 120, 90))
        self.assertGreater(residual, 15.0)

    def test_region_must_fit_with_its_margin(self):
        base = texture(3, (160, 120))
        with self.assertRaises(ValueError):
            motion.displacement(base, base, (0, 0, 50, 50))


class RegularityTests(unittest.TestCase):
    def test_uniform_alternating_and_random_series(self):
        uniform = motion.regularity([1.0] * 40, [0.0] * 40)
        self.assertEqual((uniform['irregularity'], uniform['alternation']), (0.0, 0.0))
        alternating = motion.regularity([1.3, 0.7] * 20, [0.0] * 40)
        self.assertAlmostEqual(alternating['alternation'], 0.3 * 0.8, delta=0.03)   # a 5-frame mean keeps 1/5 of it
        self.assertGreater(alternating['irregularity'], 0.2)
        rng = np.random.default_rng(7)
        noisy = motion.regularity(1.0 + rng.normal(0, 0.2, 400), np.zeros(400))
        self.assertGreater(noisy['irregularity'], 0.12)
        self.assertLess(noisy['alternation'], 0.04)   # uneven, but not at half the frame rate
        smooth = motion.regularity(np.linspace(0.5, 1.5, 60), np.zeros(60))
        self.assertLess(smooth['irregularity'], 0.01)   # an accelerating pan is not irregular

    def test_short_or_still_series_have_no_verdict(self):
        self.assertIsNone(motion.regularity([1.0] * 5, [0.0] * 5)['irregularity'])
        self.assertIsNone(motion.regularity([0.0] * 40, [0.0] * 40)['irregularity'])


class MeasureTests(unittest.TestCase):
    def test_separates_an_uneven_subject_from_a_smooth_background(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'dump'
            folder.mkdir()
            count = 40
            frames(folder, [0.8] * count, [1.4, 0.6] * (count // 2))
            (folder / 'frames.tsv').write_text('# flight dump\nframe\tt_ms\tinterval_ms\n' + ''.join(
                f'{100 + i}\t{i * 16.667:.1f}\t16.67\n' for i in range(count + 1)), encoding='utf-8')
            report = motion.measure(folder, {'background': BACKGROUND, 'subject': SUBJECT})
            self.assertEqual(report['measured_pairs'], count)
            background, subject = report['summary']['background'], report['summary']['subject']
            self.assertAlmostEqual(background['mean_step'], 0.8, delta=0.05)
            self.assertLess(background['irregularity'], 0.05)
            self.assertAlmostEqual(subject['mean_step'], 1.0, delta=0.08)
            self.assertGreater(subject['alternation'], 0.2)
            self.assertGreater(subject['irregularity'], 5 * background['irregularity'] + 0.1)
            self.assertEqual(report['summary']['present_interval_ms']['mean'], 16.67)
            # A missing frame is never bridged.
            (folder / 'f000120.png').unlink()
            self.assertEqual(motion.measure(folder, {'background': BACKGROUND})['measured_pairs'], count - 2)

    def test_cli_writes_outside_the_frame_folder_and_reads_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'dump'
            folder.mkdir()
            frames(folder, [0.5] * 12, [0.5] * 12)
            before = sorted(p.name for p in folder.iterdir())
            with patch('sys.stdout', io.StringIO()) as output:
                self.assertEqual(motion.main([str(folder), '--box', 'background:10,20,90,100',
                                              '--out', str(Path(temporary) / 'out/report.json')]), 0)
            self.assertIn('background', json.loads(output.getvalue())['summary'])
            self.assertEqual(len(json.loads((Path(temporary) / 'out/report.json').read_text())['rows']), 12)
            with patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                motion.main([str(folder), '--box', 'background:10,20,90,100', '--out', str(folder / 'report.json')])
            with patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                motion.main([str(folder), '--box', 'bad'])
            with patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                motion.main([temporary, '--box', 'background:10,20,90,100'])
            self.assertEqual(sorted(p.name for p in folder.iterdir()), before)


if __name__ == '__main__':
    unittest.main()
