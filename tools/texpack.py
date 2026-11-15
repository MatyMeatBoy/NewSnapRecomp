"""Build an HD texture pack (TEXPACK-01) from a texture dump, locally, from the player's own game.

  1. Dump: start the game with NEWSNAP_TEX_DUMP=<dump folder> and play the places to improve; each texture the game
     loads is written once as <hash>.png (newsnap/overlays/snap_texpack.c).
  2. Pack: python tools/texpack.py --dump <dump folder> --out <GameData>/texpack [--scale 2] [--min 64] [--max-edge 2048]
     Each picture is enlarged with Real-ESRGAN (toolchain/realesrgan, ncnn-vulkan: AMD, NVIDIA and Intel alike),
     brought to --scale times its size (Lanczos), and written as <hash>.dds: RGBA8 with a full mip chain, alpha kept
     from the original (enlarged with Lanczos, never invented).
  3. Play: the runtime loads texpack/<hash>.dds for the texture with that hash; AC_TEX_PACK=0 turns the pack off.

The pack holds game-derived pictures: it stays on the player's PC and is never committed or distributed.
"""
import argparse
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ESRGAN = ROOT / 'toolchain/realesrgan/realesrgan-ncnn-vulkan.exe'


def dds_rgba8(path, levels, srgb=False):
    """A DX10 DDS of RGBA8 levels (PIL images, level 0 first)."""
    w, h = levels[0].size
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x8   # caps, height, width, pixelformat, mipmapcount, pitch
    header = struct.pack('<4sIIIIIII44x', b'DDS ', 124, flags, h, w, w * 4, 0, len(levels))
    pixel = struct.pack('<II4sIIIII', 32, 0x4, b'DX10', 0, 0, 0, 0, 0)
    caps = struct.pack('<IIIII', 0x1000 | 0x400000 | 0x8, 0, 0, 0, 0)
    dx10 = struct.pack('<IIIII', 29 if srgb else 28, 3, 0, 1, 0)   # DXGI R8G8B8A8_UNORM(_SRGB), TEXTURE2D
    with open(path, 'wb') as f:
        f.write(header + pixel + caps + dx10)
        for im in levels:
            f.write(im.tobytes())


def mip_chain(img):
    levels = [img]
    while levels[-1].size != (1, 1):
        w, h = levels[-1].size
        levels.append(levels[-1].resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS))
    return levels


def enlarge(src, scale, max_edge, model, work):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    target = (w * scale, h * scale)
    if max(target) > max_edge:
        k = max_edge / max(target)
        target = (max(4, int(target[0] * k) // 4 * 4), max(4, int(target[1] * k) // 4 * 4))
    rgb_in, rgb_out = work / 'in.png', work / 'out.png'
    im.convert('RGB').save(rgb_in)
    subprocess.run([str(ESRGAN), '-i', str(rgb_in), '-o', str(rgb_out), '-n', model, '-s', '4'],
                   check=True, capture_output=True, cwd=ESRGAN.parent)
    big = Image.open(rgb_out).convert('RGB').resize(target, Image.LANCZOS)
    alpha = im.getchannel('A').resize(target, Image.LANCZOS)
    big.putalpha(alpha)
    return big


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dump', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--scale', type=int, default=2, choices=(2, 3, 4))
    ap.add_argument('--min', type=int, default=64, help='skip textures smaller than this on both sides')
    ap.add_argument('--max-edge', type=int, default=2048)
    ap.add_argument('--model', default='realesrgan-x4plus', help='realesrgan-x4plus or realesrgan-x4plus-anime')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    if not ESRGAN.is_file():
        raise SystemExit(f'Real-ESRGAN missing: {ESRGAN}')
    a.out.mkdir(parents=True, exist_ok=True)
    done = 0
    with tempfile.TemporaryDirectory(prefix='texpack-') as tmp:
        work = Path(tmp)
        for src in sorted(a.dump.glob('*.png')):
            if len(src.stem) != 16:
                continue
            dst = a.out / f'{src.stem}.dds'
            if dst.exists():
                continue
            with Image.open(src) as im:
                w, h = im.size
            if w < a.min and h < a.min:
                continue
            big = enlarge(src, a.scale, a.max_edge, a.model, work)
            dds_rgba8(dst, mip_chain(big))
            done += 1
            print(f'{src.stem}: {w}x{h} -> {big.size[0]}x{big.size[1]}', flush=True)
            if a.limit and done >= a.limit:
                break
    print(f'{done} textures written to {a.out}')


if __name__ == '__main__':
    main()
