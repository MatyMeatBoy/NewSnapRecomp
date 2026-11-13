# NewSnapRecomp icons

Original geometric camera artwork, created for this project. Forest green
`#173b31`, cream `#fff6df` and amber `#efb548`. No game artwork or extracted
resources are included.

Regenerate from the repository's pinned Pillow environment:

```powershell
python tools/generate_icons.py
python -m unittest tests.test_icons
```

`tools/generate_icons.py` contains the shared vector geometry for SVG and raster
exports. `newsnap.svg` is the scalable master export. `newsnap.ico` contains
16/24/32/48/64/128/256-pixel frames for Windows; `favicon.ico` contains 16/32/48.
PNG exports cover 16 through 512 pixels; Apple touch uses 180 pixels. The web
manifest references the 192- and 512-pixel PNGs with relative paths so the set
can be reused together. Desktop launcher code uses `newsnap.ico` and
`icon-256.png`.
