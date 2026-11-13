"""Generate original NewSnap camera icons from one shared geometric drawing.

Run ``python tools/generate_icons.py`` from any directory. Pillow is the only
dependency. SVG and all raster variants use the same shapes and palette; no
game artwork or extracted resources are used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "icons"
SIZES = (16, 24, 32, 48, 64, 128, 192, 256, 512)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
FOREST = "#173b31"
CREAM = "#fff6df"
AMBER = "#efb548"

# A 256-unit canvas. Each tuple is (kind, coordinates, fill, corner radius).
# This is the source of truth for both SVG and Pillow rendering.
SHAPES = (
    ("rect", (0, 0, 256, 256), FOREST, 52),
    ("rect", (76, 52, 143, 92), CREAM, 12),
    ("rect", (32, 76, 224, 204), CREAM, 24),
    ("rect", (178, 91, 207, 105), FOREST, 4),
    ("ellipse", (74, 94, 182, 202), FOREST, 0),
    ("ellipse", (86, 106, 170, 190), AMBER, 0),
    ("ellipse", (104, 124, 152, 172), FOREST, 0),
    ("ellipse", (112, 128, 128, 144), CREAM, 0),
)


def svg_bytes() -> bytes:
    """Serialize the geometry as an accessible, self-contained vector icon."""
    root = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "viewBox": "0 0 256 256",
        "role": "img", "aria-labelledby": "title description",
    })
    ET.SubElement(root, "title", {"id": "title"}).text = "NewSnapRecomp"
    ET.SubElement(root, "desc", {"id": "description"}).text = (
        "Original cream camera with an amber lens on a forest green tile."
    )
    for kind, (x0, y0, x1, y1), fill, radius in SHAPES:
        if kind == "rect":
            attrs = {"x": str(x0), "y": str(y0), "width": str(x1 - x0),
                     "height": str(y1 - y0), "rx": str(radius), "fill": fill}
        else:
            attrs = {"cx": str((x0 + x1) // 2), "cy": str((y0 + y1) // 2),
                     "rx": str((x1 - x0) // 2), "ry": str((y1 - y0) // 2),
                     "fill": fill}
        ET.SubElement(root, kind, attrs)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def render(size: int) -> Image.Image:
    """Supersample small icons for a clean silhouette and readable lens."""
    scale = max(4, (1024 + size - 1) // size)
    extent = size * scale
    image = Image.new("RGBA", (extent, extent), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    factor = extent / 256
    for kind, coords, fill, radius in SHAPES:
        bounds = tuple(round(value * factor) for value in coords)
        if kind == "rect":
            draw.rounded_rectangle(bounds, radius=round(radius * factor), fill=fill)
        else:
            draw.ellipse(bounds, fill=fill)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def generate(output: Path = OUTPUT) -> None:
    output.mkdir(parents=True, exist_ok=True)
    vector = svg_bytes()
    for name in ("newsnap.svg", "favicon.svg"):
        (output / name).write_bytes(vector)
    for size in SIZES:
        render(size).save(output / f"icon-{size}.png", optimize=True)
    render(180).save(output / "apple-touch-icon.png", optimize=True)
    for name, sizes in (("newsnap.ico", ICO_SIZES), ("favicon.ico", (16, 32, 48))):
        images = [render(size) for size in sizes]
        images[-1].save(output / name, format="ICO",
                        sizes=[(size, size) for size in sizes],
                        append_images=images[:-1])
    manifest = {
        "name": "NewSnapRecomp", "short_name": "NewSnap",
        "background_color": FOREST, "theme_color": FOREST,
        "icons": [{"src": f"icon-{size}.png", "sizes": f"{size}x{size}",
                   "type": "image/png", "purpose": "any"} for size in (192, 512)],
    }
    (output / "site.webmanifest").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT,
                        help="destination directory (default: assets/icons)")
    generate(parser.parse_args().output)
