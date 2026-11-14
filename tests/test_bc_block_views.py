"""FOTO-01: the 2D BC stand-in seams apply once each to the pinned donor runtime."""
from pathlib import Path
import unittest

from newsnap.bc_block_views_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'third_party/astral'


class BcBlockViewsAdapt(unittest.TestCase):
    def adapted(self, name):
        text = (RUNTIME / name).read_text(encoding='utf-8')
        for before, after in edits()[name]:
            self.assertEqual(text.count(before), 1, f'{name}: seam changed: {before[:60]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_texture_default_follows_rdna12_driver(self):
        text = self.adapted('runtime/vk_texture.c')
        self.assertIn('rt_knob("BLOCK_VIEWS", vk_caps.amd_sc ? "0" : "1")', text)
        self.assertIn('(type == VK_IMAGE_TYPE_3D ? bv3d : bv2d)', text)
        self.assertNotIn('(type != VK_IMAGE_TYPE_3D || bv3d)', text)

    def test_exec_routes_2d_bc_targets_through_refreshed_stand_ins(self):
        text = self.adapted('runtime/vk_exec.c')
        self.assertIn('img->type != VK_IMAGE_TYPE_3D && img->type != VK_IMAGE_TYPE_2D', text)
        self.assertIn('static void bc_refresh(VkExec *ex, const VkExecTarget *t)', text)
        # refresh happens after the pass-begin barrier, before rendering starts
        begin = text.index('void vk_exec_pass_begin(VkExec *ex)')
        self.assertLess(text.index('bc_refresh(ex, &ex->color[i])', begin), text.index('vkCmdBeginRendering', begin))
        # a direct whole-image clear must never land only in a stand-in
        self.assertIn('(t->img && t->img->image != t->image)', text)

    def test_cfg_knows_the_key(self):
        self.assertIn('"BLOCK_VIEWS", "BLOCK_VIEWS_3D"', self.adapted('runtime/cfg.c'))

    def test_registered_in_adapt(self):
        source = (ROOT / 'newsnap/adapt.py').read_text(encoding='utf-8')
        self.assertIn('bc_block_views_edits', source.split('for adapter in', 1)[1])


if __name__ == '__main__':
    unittest.main()
