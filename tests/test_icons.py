"""Check generated assets and every embedded Windows icon frame."""

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

from tools.generate_icons import ICO_SIZES, OUTPUT, SIZES, generate, svg_bytes
from newsnap.adapt import adapt_sources


class IconTests(unittest.TestCase):
    def test_game_resource_uses_original_project_artwork(self):
        with tempfile.TemporaryDirectory() as directory:
            source = adapt_sources(Path(directory))
            self.assertEqual((source / 'runtime/astralchain.ico').read_bytes(),
                             (OUTPUT / 'newsnap.ico').read_bytes())

    def test_png_dimensions_and_transparency(self):
        expected = {f"icon-{size}.png": size for size in SIZES}
        expected["apple-touch-icon.png"] = 180
        for name, size in expected.items():
            with self.subTest(name=name), Image.open(OUTPUT / name) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (size, size))
                self.assertEqual(image.mode, "RGBA")
                self.assertLessEqual(image.getpixel((0, 0))[3], 2)
                self.assertEqual(image.getpixel((size // 2, size // 2))[3], 255)
                image.load()

    def test_all_ico_frames_decode(self):
        for name, sizes in (("newsnap.ico", ICO_SIZES), ("favicon.ico", (16, 32, 48))):
            with self.subTest(name=name), Image.open(OUTPUT / name) as image:
                self.assertEqual(image.format, "ICO")
                self.assertEqual(image.ico.sizes(), {(size, size) for size in sizes})
                for size in sizes:
                    frame = image.ico.getimage((size, size))
                    frame.load()
                    self.assertEqual(frame.size, (size, size))
                    self.assertEqual(frame.mode, "RGBA")

    def test_vectors_and_manifest_references(self):
        for name in ("newsnap.svg", "favicon.svg"):
            data = (OUTPUT / name).read_bytes()
            root = ET.fromstring(data)
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertEqual(root.attrib["viewBox"], "0 0 256 256")
            self.assertEqual(data, svg_bytes())
        manifest = json.loads((OUTPUT / "site.webmanifest").read_text(encoding="utf-8"))
        for icon in manifest["icons"]:
            with Image.open(OUTPUT / icon["src"]) as image:
                self.assertEqual(icon["sizes"], f"{image.width}x{image.height}")

    def test_regeneration_matches_checked_in_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory)
            generate(generated)
            self.assertEqual({p.name for p in generated.iterdir()},
                             {p.name for p in OUTPUT.iterdir() if p.suffix != ".md"})
            for path in generated.iterdir():
                checked_in = OUTPUT / path.name
                if path.suffix in ('.png', '.ico'):
                    # zlib versions can encode identical pixels differently.
                    with Image.open(path) as actual, Image.open(checked_in) as expected:
                        sizes = actual.ico.sizes() if path.suffix == '.ico' else {actual.size}
                        if path.suffix == '.ico':
                            self.assertEqual(sizes, expected.ico.sizes())
                        for size in sizes:
                            a = actual.ico.getimage(size) if path.suffix == '.ico' else actual
                            b = expected.ico.getimage(size) if path.suffix == '.ico' else expected
                            self.assertEqual(a.convert('RGBA').tobytes(), b.convert('RGBA').tobytes(), path.name)
                else:
                    self.assertEqual(path.read_text(), checked_in.read_text(), path.name)


if __name__ == "__main__":
    unittest.main()
