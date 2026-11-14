"""PIPE-MO-01: per-object motion pipeline records name their shader and the prewarm recreates it."""
from pathlib import Path
import unittest

from newsnap.pipe_mo_keys_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'third_party/astral'


class PipeMoKeysAdapt(unittest.TestCase):
    def adapted(self, name):
        text = (RUNTIME / name).read_text(encoding='utf-8')
        for before, after in edits()[name]:
            self.assertEqual(text.count(before), 1, f'{name}: seam changed: {before[:60]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_draw_side_exports_the_location_lookup(self):
        text = self.adapted('runtime/vk_exec_draw.c')
        self.assertLess(text.index('static const GfxShader *mo_fs(int loc)'), text.index('int snap_mo_fs_location('))
        self.assertIn('const GfxShader *snap_mo_fs_get(int loc) { return mo_fs(loc); }', text)

    def test_records_are_tagged_and_recreated(self):
        text = self.adapted('runtime/vk_pipeline.c')
        fill = text[text.index('static void rec_fill('):]
        self.assertIn('r->pad = SNAP_MO_KEY_TAG | (uint32_t)loc;', fill[:fill.index('\n}\n')])
        warm = text[text.index('uint32_t queued = 0, dropped = 0, known = 0, snap_mo = 0;'):]
        self.assertLess(warm.index('snap_mo_fs_get((int)(r[i].pad & 0xffu))'), warm.index('dropped++;'))
        self.assertIn('per-object motion pipelines recreated', warm)

    def test_keyrec_layout_keeps_its_spare_word(self):
        text = (RUNTIME / 'runtime/vk_pipeline.c').read_text(encoding='utf-8')
        self.assertIn('    uint32_t has_fs, pad;', text)   # the tag lives in the existing pad: record size unchanged


if __name__ == '__main__':
    unittest.main()
