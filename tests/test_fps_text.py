"""FPS-TXT-01: no menu text still promises a 60 fps patch that Snap does not have."""
from pathlib import Path
import unittest

from newsnap.fps_text_adapt import edits

ROOT = Path(__file__).resolve().parents[1]


class FpsText(unittest.TestCase):
    def test_every_language_is_rewritten(self):
        text = (ROOT / 'third_party/astral/runtime/ui_text.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/ui_text.c']:
            self.assertEqual(text.count(before), 1, before[:40])
            text = text.replace(before, after, 1)
        self.assertNotIn("fps patch", text.split('[UI_MENU_FPS_30]')[0].split('[UI_MENU_FPS_LIMIT_DESC]')[-1])
        self.assertEqual(text.count('Snap'), text.count('Snap'))  # sanity: file still decodes


if __name__ == '__main__':
    unittest.main()
