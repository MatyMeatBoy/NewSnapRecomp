"""GYRO-02: the gyro sensitivity seams apply to the pinned donor and the launcher offers the setting."""
from pathlib import Path
import unittest

from newsnap.gyro_sens_adapt import edits
from newsnap import launcher_settings as settings

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'third_party/astral'


class GyroSensAdapt(unittest.TestCase):
    def adapted(self, name):
        text = (RUNTIME / name).read_text(encoding='utf-8')
        for before, after in edits()[name]:
            self.assertEqual(text.count(before), 1, f'{name}: seam changed: {before[:60]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_rate_is_scaled_before_integration_and_pull_only_at_scale_one(self):
        text = self.adapted('runtime/motion_fusion.c')
        feed = text[text.index('void motion_feed('):]
        self.assertLess(feed.index('snap_gyro_scale()'), feed.index('plat_mutex_lock(&m->lock)'))
        self.assertIn('integrate(m->R, gyro, acc, dt, k == 1.0)', feed)
        self.assertIn('if (pull && fabs(n - 1) < 0.15)', text)
        self.assertIn('cfg_double("AC_GYRO_SENS")', text)

    def test_cfg_default_and_section(self):
        text = self.adapted('runtime/cfg.c')
        self.assertIn('{"GYRO_SENS", "2.5", "0.1..10", LIVE}', text)
        self.assertIn('{"GYRO_SENS", "input"}', text)
        self.assertIn('"GYRO_SENS"', text.split('{"GYRO_SENS", "input"}')[0])

    def test_launcher_setting(self):
        self.assertEqual(settings.DEFAULTS['gyro_sens'], '2.5')
        self.assertEqual(settings.SECTIONS['gyro_sens'], 'input')
        self.assertEqual(settings.validate_settings({'gyro_sens': '5'}), {'gyro_sens': '5'})
        for bad in ('0', '11', 'nan', 'fast'):
            with self.assertRaises(ValueError):
                settings.validate_settings({'gyro_sens': bad})

    def test_launcher_has_aim_options_in_controls(self):
        source = (ROOT / 'newsnap/launcher.py').read_text(encoding='utf-8')
        mods = source[source.index('def _aim_options(self, content):'):]
        for key in ("'motion'", "'gyro_sens'", "'mouse_sens'"):
            self.assertIn(key, mods.split('def export_diagnostics')[0])


if __name__ == '__main__':
    unittest.main()
