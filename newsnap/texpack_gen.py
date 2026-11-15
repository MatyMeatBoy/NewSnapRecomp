"""HD texture pack generation (TEXPACK-01), from the launcher or the command line.

With «Guardar texturas para el pack» (AC_TEX_PACK_SAVE=1) the runtime writes each colour texture it loads, once, as
<GameData>/texpack/src/<hash>.png (newsnap/overlays/snap_texpack.c). This turns them into <GameData>/texpack/<hash>.dds,
which the runtime uses in their place by hash (AC_TEX_PACK):

  1. Real-ESRGAN (realesrgan-x4plus) enlarges the colour; alpha is enlarged with Lanczos, never invented.
  2. The result is brought to --scale times the original (Lanczos), at most --max-edge texels.
  3. A full mip chain is encoded to BC1 (opaque) or BC3 (with alpha), sRGB, by this file: 4 or 8 bits per texel,
     so a pack costs a quarter or an eighth of plain RGBA8 video memory.

    python -m newsnap.texpack_gen --dir <GameData>/texpack [--scale 2] [--min 64] [--max-edge 2048] [--limit N]

The pack holds game-derived pictures: it stays on the player's PC and is never committed or distributed.
"""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image

from .hdshadows import ESRGAN, ensure_esrgan


# ---- BC1 / BC3 -----------------------------------------------------------------------------------------------------

def _blocks(rgba):
    h, w, c = rgba.shape
    return rgba.reshape(h // 4, 4, w // 4, 4, c).transpose(0, 2, 1, 3, 4).reshape(-1, 16, c).astype(np.float64)


def _to565(rgb):
    r = np.clip(np.rint(rgb[:, 0] * 31 / 255), 0, 31).astype(np.uint32)
    g = np.clip(np.rint(rgb[:, 1] * 63 / 255), 0, 63).astype(np.uint32)
    b = np.clip(np.rint(rgb[:, 2] * 31 / 255), 0, 31).astype(np.uint32)
    return (r << 11) | (g << 5) | b


def _from565(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], axis=1).astype(np.float64)


def _colour_blocks(px):
    """BC1 colour part (4-colour mode) of blocks px (N, 16, 3): (N,) uint64."""
    mean = px.mean(axis=1, keepdims=True)
    centred = px - mean
    cov = np.einsum('nki,nkj->nij', centred, centred)
    axis = np.ones((len(px), 3))
    for _ in range(4):
        axis = np.einsum('nij,nj->ni', cov, axis)
        axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
    t = np.einsum('nki,ni->nk', centred, axis)
    hi = np.clip(mean[:, 0] + t.max(1)[:, None] * axis, 0, 255)
    lo = np.clip(mean[:, 0] + t.min(1)[:, None] * axis, 0, 255)
    c0, c1 = _to565(hi), _to565(lo)
    swap = c0 < c1
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    e0, e1 = _from565(c0), _from565(c1)
    palette = np.stack([e0, e1, (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3], axis=1)
    idx = ((px[:, :, None, :] - palette[:, None, :, :]) ** 2).sum(3).argmin(2).astype(np.uint64)
    same = c0 == c1   # one colour: the 4-colour mode needs c0 > c1, index 0 everywhere still decodes c0
    idx[same] = 0
    bits = np.zeros(len(px), dtype=np.uint64)
    for i in range(16):
        bits |= idx[:, i] << np.uint64(2 * i)
    return c0.astype(np.uint64) | (c1.astype(np.uint64) << np.uint64(16)) | (bits << np.uint64(32))


def _alpha_blocks(a):
    """BC4 part of BC3 for alpha (N, 16): (N,) uint64, 8-value mode."""
    a0 = a.max(1).astype(np.int64)
    a1 = a.min(1).astype(np.int64)
    flat = a0 == a1
    a1 = np.where(flat, np.maximum(a0 - 1, 0), a1)
    a0 = np.where(flat & (a0 == 0), 1, a0)
    pal = np.stack([a0, a1] + [((7 - k) * a0 + k * a1) / 7 for k in range(1, 7)], axis=1).astype(np.float64)
    idx = np.abs(a[:, :, None] - pal[:, None, :]).argmin(2).astype(np.uint64)
    bits = np.zeros(len(a), dtype=np.uint64)
    for i in range(16):
        bits |= idx[:, i] << np.uint64(3 * i)
    return a0.astype(np.uint64) | (a1.astype(np.uint64) << np.uint64(8)) | (bits << np.uint64(16))


def encode(rgba, alpha):
    """rgba uint8 (H, W, 4) with H, W multiples of 4: BC3 when alpha else BC1, as bytes."""
    b = _blocks(rgba)
    colour = _colour_blocks(b[:, :, :3])
    if not alpha:
        return colour.astype('<u8').tobytes()
    return np.stack([_alpha_blocks(b[:, :, 3]), colour], axis=1).astype('<u8').tobytes()


def decode_bc1(blob, w, h):
    """Colour of BC1 blocks (4-colour mode, as encode writes them), for the tests: uint8 (H, W, 3)."""
    words = np.frombuffer(blob, dtype='<u8').astype(np.uint64)
    c0, c1 = (words & np.uint64(0xFFFF)).astype(np.uint32), ((words >> np.uint64(16)) & np.uint64(0xFFFF)).astype(np.uint32)
    e0, e1 = _from565(c0), _from565(c1)
    palette = np.stack([e0, e1, (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3], axis=1)
    idx = np.stack([((words >> np.uint64(32 + 2 * i)) & np.uint64(3)).astype(np.int64) for i in range(16)], axis=1)
    px = np.take_along_axis(palette, idx[:, :, None].repeat(3, 2), axis=1)
    return np.rint(px.reshape(h // 4, w // 4, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(h, w, 3)).astype(np.uint8)


def write_dds(path, levels, alpha):
    """levels: [(w, h, bytes)] BC1/BC3 sRGB, level 0 first."""
    w, h = levels[0][0], levels[0][1]
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000
    header = struct.pack('<4sIIIIIII44x', b'DDS ', 124, flags, h, w, len(levels[0][2]), 0, len(levels))
    pixel = struct.pack('<II4sIIIII', 32, 0x4, b'DX10', 0, 0, 0, 0, 0)
    caps = struct.pack('<IIIII', 0x1000 | 0x400000 | 0x8, 0, 0, 0, 0)
    dx10 = struct.pack('<IIIII', 78 if alpha else 72, 3, 0, 1, 0)   # BC3_UNORM_SRGB / BC1_UNORM_SRGB
    tmp = Path(str(path) + '.part')
    with open(tmp, 'wb') as f:
        f.write(header + pixel + caps + dx10)
        for _w, _h, blob in levels:
            f.write(blob)
    tmp.replace(path)


# ---- pack ----------------------------------------------------------------------------------------------------------

def enlarge(src, scale, max_edge, work, model='realesrgan-x4plus'):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    target = (w * scale, h * scale)
    if max(target) > max_edge:
        k = max_edge / max(target)
        target = (int(target[0] * k), int(target[1] * k))
    target = (max(4, target[0] // 4 * 4), max(4, target[1] // 4 * 4))
    rgb_in, rgb_out = work / 'in.png', work / 'out.png'
    im.convert('RGB').save(rgb_in)
    subprocess.run([str(ESRGAN), '-i', str(rgb_in), '-o', str(rgb_out), '-n', model, '-s', '4'],
                   check=True, capture_output=True, cwd=ESRGAN.parent)
    big = Image.open(rgb_out).convert('RGB').resize(target, Image.LANCZOS)
    big.putalpha(im.getchannel('A').resize(target, Image.LANCZOS))
    return big


def build(src, dst, scale, max_edge, work):
    big = enlarge(src, scale, max_edge, work)
    alpha = big.getchannel('A').getextrema()[0] < 250
    levels, level = [], big
    while True:
        w, h = level.size[0] // 4 * 4, level.size[1] // 4 * 4
        if w < 4 or h < 4:
            break
        arr = np.asarray(level.crop((0, 0, w, h)), dtype=np.uint8)
        levels.append((w, h, encode(arr, alpha)))
        if min(w, h) <= 4:
            break
        level = level.resize((max(4, level.size[0] // 2), max(4, level.size[1] // 2)), Image.LANCZOS)
    write_dds(dst, levels, alpha)
    return big.size


def pending(folder, minimum=64):
    out = []
    for src in sorted((Path(folder) / 'src').glob('*.png')):
        if len(src.stem) != 16 or (Path(folder) / f'{src.stem}.dds').exists() or (Path(folder) / f'{src.stem}.skip').exists():
            continue
        out.append(src)
    return out


def generate(folder, scale=2, minimum=64, max_edge=2048, limit=0, report=print, cancel=None):
    folder = Path(folder)
    todo = pending(folder, minimum)
    if limit:
        todo = todo[:limit]
    made = failed = 0
    with tempfile.TemporaryDirectory(prefix='texpack-') as tmp:
        for n, src in enumerate(todo, 1):
            if cancel is not None and cancel.is_set():
                break
            with Image.open(src) as im:
                w, h = im.size
            if w < minimum and h < minimum:
                (folder / f'{src.stem}.skip').write_bytes(b'')
                continue
            try:
                build(src, folder / f'{src.stem}.dds', scale, max_edge, Path(tmp))
                made += 1
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                failed += 1
                report(f'[{n}/{len(todo)}] {src.stem}: sin procesar ({error})')
                continue
            report(f'Pack de texturas HD: {n}/{len(todo)} texturas')
    return made, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', type=Path, required=True, help='<GameData>/texpack')
    ap.add_argument('--scale', type=int, default=2, choices=(2, 3, 4))
    ap.add_argument('--min', type=int, default=64)
    ap.add_argument('--max-edge', type=int, default=2048)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args(argv)
    ensure_esrgan()
    made, failed = generate(a.dir, a.scale, a.min, a.max_edge, a.limit, report=lambda t: print(t, flush=True))
    print(f'{made} HD textures written, {failed} failed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
