"""PRESENT-WIN-01: a composited window takes immediate when mailbox is missing; borderless keeps FIFO."""
from pathlib import Path
import unittest

from newsnap.windowed_present_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'third_party/astral'


class WindowedPresentAdapt(unittest.TestCase):
    def adapted(self, name):
        text = (RUNTIME / name).read_text(encoding='utf-8')
        for before, after in edits()[name]:
            self.assertEqual(text.count(before), 1, f'{name}: seam changed: {before[:60]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_only_when_mailbox_is_missing_and_the_window_is_smaller_than_its_monitor(self):
        text = self.adapted('runtime/gfx_present.c')
        pick = text[text.index('static VkPresentModeKHR pick_present_mode('):]
        pick = pick[:pick.index('\n}\n')]
        self.assertIn('want == VK_PRESENT_MODE_MAILBOX_KHR && got != want && rt_knob("WINDOWED_IMMEDIATE", "1")', pick)
        self.assertIn('(cw < mw || ch < mh)', pick)
        self.assertIn('if (m[i] == VK_PRESENT_MODE_IMMEDIATE_KHR) got = m[i];', pick)
        self.assertLess(pick.index('got = want;'), pick.index('WINDOWED_IMMEDIATE'))
        self.assertLess(pick.index('WINDOWED_IMMEDIATE'), pick.index('const char *name'))

    def test_cfg_knows_the_key(self):
        self.assertIn('"WINDOWED_IMMEDIATE"', self.adapted('runtime/cfg.c'))


if __name__ == '__main__':
    unittest.main()
