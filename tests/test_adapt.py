import tempfile
import unittest
from pathlib import Path

from newsnap.adapt import adapt_sources
from newsnap.upstream import UPSTREAM


class AdaptTests(unittest.TestCase):
    def test_layout_never_inherits_astral_romfs_address(self):
        with tempfile.TemporaryDirectory() as folder:
            dst = Path(folder) / 'src'
            adapt_sources(dst)
            layout = (dst / 'recomp/layout.py').read_text()
            boot = (dst / 'runtime/boot.c').read_text()
            self.assertIn("'snap': 0", layout)
            self.assertIn('return 0  # Snap uses nn::fs', layout)
            self.assertIn('stack != 0x4000', boot)
            self.assertIn('#define MAIN_STACK 0x4000ull', (dst / 'runtime/kernel.c').read_text())
            self.assertIn("EXE = 'newsnap.exe'", (dst / 'tools/build_game.py').read_text())
            # Upstream stays pristine; this also keeps patches independently reviewable.
            self.assertNotIn("'snap': 0", (UPSTREAM / 'recomp/layout.py').read_text())


if __name__ == '__main__':
    unittest.main()
