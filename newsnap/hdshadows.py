"""HD shadows (HD-SHADOW-01): enlarge the light maps the game bakes its scenery shadows into.

The game's shadows of plants, rocks and scenery are baked into each level's light maps (single-level BC6H textures,
128x128 to 512x512). With AC_HD_SHADOWS=1 the runtime writes each light map it loads, once, as float to
<GameData>/hdshadows/src/<hash>.dds (newsnap/overlays/snap_texpack.c). This tool turns them into
<GameData>/hdshadows/<hash>.dds, which the runtime uses in their place the next time they load:

  1. The empty texels between the UV islands are filled from the islands' edges (push-pull), so enlarging and
     filtering do not pull black into the islands' borders (seams on the ground).
  2. The light is encoded as log2(1 + value) to 8 bits and enlarged with Real-ESRGAN (toolchain/realesrgan,
     realesr-animevideov3: clean edges without invented texture), then decoded back to float.
  3. The low frequencies are matched to a plain enlargement of the original, so the amount of light, its colour
     and the overall brightness stay the game's; only the edges of the shadows get sharper and smoother.
  4. Mips are made and each level is encoded to BC6H (unsigned half floats, mode 11) by this file.

Maps with negative values hold directional terms of the lighting, not light; they are left as they are (a .skip
file records it).

    python -m newsnap.hdshadows --dir <GameData>/hdshadows [--scale 2] [--limit N]
    (the launcher's «Generar sombras HD» runs the same, fetching Real-ESRGAN first when it is missing)

The light maps are game-derived pictures: they stay on the player's PC and are never committed or distributed.
"""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image

from .upstream import ROOT

ESRGAN = ROOT / 'toolchain/realesrgan/realesrgan-ncnn-vulkan.exe'
# Real-ESRGAN ncnn-vulkan v0.2.5.0 (BSD-3-Clause), fetched only when the player asks for HD shadows. The files used
# are pinned; anything else in the archive is not extracted.
ESRGAN_URL = ('https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/'
              'realesrgan-ncnn-vulkan-20220424-windows.zip')
ESRGAN_FILES = {
    'realesrgan-ncnn-vulkan.exe': '07e49f7cbb4ede01ae4dd4c399d3a7e5846e3d2085c3128eff881e55cb7b1a0c',
    'models/realesr-animevideov3-x2.bin': '548a36f9c3f4ab8da56cd3b13badf23968bee207b396dad14d04b830e5f2ab2d',
    'models/realesr-animevideov3-x2.param': 'b88ff4f00ebf019a7fdac17fdd45a7fd3665d37509efc5baf2e4da2e24420a04',
    'models/realesrgan-x4plus.bin': '713ee713b0353afaa27976f0563a64a5043bd70b9bd8936c2e26e25ebcdbcddf',
    'models/realesrgan-x4plus.param': '35330ececcea33b6c397a72548e788d5d53becee4734c50b7fada36e89f10a86',
}


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def esrgan_ready():
    folder = ESRGAN.parent
    return all((folder / name).is_file() and _sha256(folder / name) == digest for name, digest in ESRGAN_FILES.items())


def ensure_esrgan(report=print):
    """Real-ESRGAN in toolchain/realesrgan, downloaded from its official release and checked file by file."""
    if esrgan_ready():
        return
    import io
    import urllib.request
    import zipfile
    report('Descargando la herramienta de escalado (unos 45 MB, una sola vez)…')
    with urllib.request.urlopen(ESRGAN_URL, timeout=120) as response:
        data = response.read(200 << 20)
    folder = ESRGAN.parent
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        wanted = set(ESRGAN_FILES) | {'vcomp140.dll', 'vcomp140d.dll'}
        for member in archive.namelist():
            # the files at the archive's top or under one folder; nothing else is extracted
            name = next((n for n in (member, member.split('/', 1)[-1]) if n in wanted), None)
            if name is None:
                continue
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    if not esrgan_ready():
        raise ValueError('La herramienta de escalado descargada no coincide con la versión esperada')
FLOOR = 1.0 / 1024   # light below this is treated as black by the log encoding
WEIGHTS4 = np.array([0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64], dtype=np.int64)


# ---- DDS ---------------------------------------------------------------------------------------------------------

def read_dds_rgba16f(path):
    data = Path(path).read_bytes()
    if data[:4] != b'DDS ' or data[84:88] != b'DX10' or struct.unpack_from('<I', data, 128)[0] != 10:
        raise ValueError(f'{path}: not an RGBA16F DDS')
    height, width = struct.unpack_from('<II', data, 12)
    px = np.frombuffer(data, dtype=np.float16, count=width * height * 4, offset=148)
    return px.reshape(height, width, 4)[..., :3].astype(np.float32)


def write_dds_bc6h(path, levels):
    """levels: list of (width, height, bytes) for BC6H_UF16, level 0 first."""
    w, h = levels[0][0], levels[0][1]
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000   # caps, height, width, pixelformat, mipmapcount, linearsize
    header = struct.pack('<4sIIIIIII44x', b'DDS ', 124, flags, h, w, len(levels[0][2]), 0, len(levels))
    pixel = struct.pack('<II4sIIIII', 32, 0x4, b'DX10', 0, 0, 0, 0, 0)
    caps = struct.pack('<IIIII', 0x1000 | 0x400000 | 0x8, 0, 0, 0, 0)
    dx10 = struct.pack('<IIIII', 95, 3, 0, 1, 0)   # DXGI_FORMAT_BC6H_UF16, TEXTURE2D
    tmp = Path(str(path) + '.part')
    with open(tmp, 'wb') as f:
        f.write(header + pixel + caps + dx10)
        for _w, _h, blob in levels:
            f.write(blob)
    tmp.replace(path)


# ---- BC6H (mode 11: one region, 10-bit endpoints, 4-bit indices, unsigned) ------------------------------------------

def _unquantize(q):
    q = q.astype(np.int64)
    return np.where(q == 0, 0, np.where(q == 1023, 0xFFFF, q * 64 + 32))


def encode_bc6h(rgb):
    """rgb: float32 (H, W, 3), H and W multiples of 4, values >= 0. Returns the BC6H_UF16 blocks as bytes."""
    h, w, _ = rgb.shape
    half = np.clip(rgb, 0, 65504).astype(np.float16).view(np.uint16).astype(np.float64)
    x = half * 64.0 / 31.0                                  # the interpolation domain (finish: unq * 31 >> 6)
    blocks = x.reshape(h // 4, 4, w // 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 3)
    mean = blocks.mean(axis=1, keepdims=True)
    centred = blocks - mean
    cov = np.einsum('nki,nkj->nij', centred, centred)
    axis = np.ones((len(blocks), 3))
    for _ in range(6):                                       # principal direction by power iteration
        axis = np.einsum('nij,nj->ni', cov, axis)
        axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-12)
    t = np.einsum('nki,ni->nk', centred, axis)
    e0 = np.clip(mean[:, 0] + t.min(axis=1)[:, None] * axis, 0, 65535)
    e1 = np.clip(mean[:, 0] + t.max(axis=1)[:, None] * axis, 0, 65535)
    for refine in range(3):
        q0 = np.clip(np.rint((e0 - 32) / 64), 0, 1023).astype(np.int64)
        q1 = np.clip(np.rint((e1 - 32) / 64), 0, 1023).astype(np.int64)
        u0, u1 = _unquantize(q0), _unquantize(q1)
        palette = (u0[:, None, :] * (64 - WEIGHTS4)[None, :, None] + u1[:, None, :] * WEIGHTS4[None, :, None] + 32) >> 6
        dist = ((blocks[:, :, None, :] - palette[:, None, :, :]) ** 2).sum(axis=3)
        idx = dist.argmin(axis=2).astype(np.int64)
        if refine == 2:
            break
        # least-squares endpoints for the chosen weights, then choose the indices again
        wt = WEIGHTS4[idx] / 64.0
        a, b = 1.0 - wt, wt
        aa, bb, ab = (a * a).sum(1), (b * b).sum(1), (a * b).sum(1)
        ax, bx = np.einsum('nk,nkc->nc', a, blocks), np.einsum('nk,nkc->nc', b, blocks)
        det = aa * bb - ab * ab
        ok = det > 1e-9
        d = np.where(ok, det, 1.0)[:, None]
        e0 = np.where(ok[:, None], np.clip((bb[:, None] * ax - ab[:, None] * bx) / d, 0, 65535), e0)
        e1 = np.where(ok[:, None], np.clip((aa[:, None] * bx - ab[:, None] * ax) / d, 0, 65535), e1)
    swap = idx[:, 0] >= 8                                    # the anchor index has no top bit
    q0[swap], q1[swap] = q1[swap].copy(), q0[swap].copy()
    idx[swap] = 15 - idx[swap]
    q0u, q1u, idxu = q0.astype(np.uint64), q1.astype(np.uint64), idx.astype(np.uint64)
    lo = np.full(len(blocks), 3, dtype=np.uint64)            # mode 11: bits 00011
    lo |= q0u[:, 0] << np.uint64(5)
    lo |= q0u[:, 1] << np.uint64(15)
    lo |= q0u[:, 2] << np.uint64(25)
    lo |= q1u[:, 0] << np.uint64(35)
    lo |= q1u[:, 1] << np.uint64(45)
    lo |= (q1u[:, 2] & np.uint64(0x1FF)) << np.uint64(55)
    hi = q1u[:, 2] >> np.uint64(9)
    hi |= idxu[:, 0] << np.uint64(1)
    for i in range(1, 16):
        hi |= idxu[:, i] << np.uint64(4 + (i - 1) * 4)
    return np.stack([lo, hi], axis=1).astype('<u8').tobytes()


def decode_bc6h(blob, width, height):
    """Mode 11 blocks only (what encode_bc6h writes): float32 (H, W, 3). For the tests."""
    words = np.frombuffer(blob, dtype='<u8').reshape(-1, 2)
    lo, hi = words[:, 0].astype(np.uint64), words[:, 1].astype(np.uint64)
    if np.any((lo & np.uint64(0x1F)) != 3):
        raise ValueError('not a mode 11 block')
    field = lambda v, s, n: ((v >> np.uint64(s)) & np.uint64((1 << n) - 1)).astype(np.int64)
    q0 = np.stack([field(lo, 5, 10), field(lo, 15, 10), field(lo, 25, 10)], axis=1)
    q1 = np.stack([field(lo, 35, 10), field(lo, 45, 10), field(lo, 55, 9) | (field(hi, 0, 1) << 9)], axis=1)
    idx = np.stack([field(hi, 1, 3)] + [field(hi, 4 + (i - 1) * 4, 4) for i in range(1, 16)], axis=1)
    u0, u1 = _unquantize(q0), _unquantize(q1)
    wt = WEIGHTS4[idx]
    v = (u0[:, None, :] * (64 - wt)[:, :, None] + u1[:, None, :] * wt[:, :, None] + 32) >> 6
    halfbits = ((v * 31) >> 6).astype(np.uint16)
    out = halfbits.view(np.float16).astype(np.float32)
    return out.reshape(height // 4, width // 4, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(height, width, 3)


# ---- light map processing ----------------------------------------------------------------------------------------

def fill_empty(rgb, mask):
    """Push-pull: texels outside the UV islands take the average of the nearest island texels."""
    if mask.all() or not mask.any():
        return rgb
    levels = [(rgb * mask[..., None], mask.astype(np.float32))]
    while min(levels[-1][1].shape) > 1:
        c, m = levels[-1]
        h, w = (c.shape[0] + 1) // 2 * 2, (c.shape[1] + 1) // 2 * 2
        c = np.pad(c, ((0, h - c.shape[0]), (0, w - c.shape[1]), (0, 0)))
        m = np.pad(m, ((0, h - m.shape[0]), (0, w - m.shape[1])))
        cs = c.reshape(h // 2, 2, w // 2, 2, 3).sum(axis=(1, 3))
        ms = m.reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))
        levels.append((cs, ms))
    colour = levels[-1][0] / np.maximum(levels[-1][1], 1e-6)[..., None]
    for c, m in reversed(levels[:-1]):
        up = np.repeat(np.repeat(colour, 2, axis=0), 2, axis=1)[:c.shape[0], :c.shape[1]]
        here = c / np.maximum(m, 1e-6)[..., None]
        colour = np.where((m > 0)[..., None], here, up)
    return np.where(mask[..., None], rgb, colour)


def _resize_float(rgb, size, resample=Image.BICUBIC):
    return np.stack([np.asarray(Image.fromarray(rgb[..., i]).resize(size, resample)) for i in range(3)], axis=2)


def _blur(rgb, sigma):
    """Separable Gaussian blur of a float image, edges repeated."""
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.pad(rgb, ((r, r), (0, 0), (0, 0)), mode='edge')
    out = sum(k[i] * out[i:i + rgb.shape[0]] for i in range(2 * r + 1))
    out = np.pad(out, ((0, 0), (r, r), (0, 0)), mode='edge')
    return sum(k[i] * out[:, i:i + rgb.shape[1]] for i in range(2 * r + 1)).astype(np.float32)


def enlarge(rgb, scale, work, model='realesr-animevideov3'):
    h, w, _ = rgb.shape
    mask = rgb.max(axis=2) > 1e-6
    filled = fill_empty(rgb, mask)
    # a true log scale between the darkest and brightest light of this map: the 8 bits the upscaler takes are spread
    # over stops of light, so the dark side of a shadow keeps as much detail as the lit side
    logv = np.log2(np.maximum(filled, 0) + FLOOR)
    low = float(logv[mask].min()) if mask.any() else float(logv.min())
    top = max(float(logv.max()) - low, 1e-6)
    pic = np.clip(np.rint((logv - low) / top * 255.0), 0, 255).astype(np.uint8)
    src, dst = work / 'in.png', work / 'out.png'
    Image.fromarray(pic, 'RGB').save(src)
    subprocess.run([str(ESRGAN), '-i', str(src), '-o', str(dst), '-n', model, '-s', str(scale)],
                   check=True, capture_output=True, cwd=ESRGAN.parent,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))   # no console window per picture
    big = np.asarray(Image.open(dst).convert('RGB'), dtype=np.float32)
    size = (w * scale, h * scale)
    if big.shape[:2] != (size[1], size[0]):
        big = np.asarray(Image.fromarray(big.astype(np.uint8)).resize(size, Image.LANCZOS), dtype=np.float32)
    out = np.maximum(np.exp2(big / 255.0 * top + low) - FLOOR, 0)
    plain = np.maximum(_resize_float(filled, size), 0)
    radius = 1.5 * scale
    ratio = (_blur(plain, radius) + 1e-4) / (_blur(out, radius) + 1e-4)
    out = np.maximum(out * np.clip(ratio, 0.6, 1.6), 0)
    # texels that were empty (0) stay empty: the fill only keeps black out of the islands' borders while enlarging
    keep = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize(size, Image.NEAREST)) > 0
    return np.where(keep[..., None], out, 0).astype(np.float32)


def mip_levels(rgb):
    levels = [rgb]
    while min(levels[-1].shape[:2]) > 4:
        c = levels[-1]
        h, w = c.shape[0] // 2 * 2, c.shape[1] // 2 * 2
        levels.append(c[:h, :w].reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3)))
    return levels


def is_signed(rgb):
    """Light maps with negative values hold directional terms of the lighting, not light: they are left as they are."""
    return float((rgb < 0).mean()) > 0.001


def build(src, dst, scale, work):
    rgb = read_dds_rgba16f(src)
    if is_signed(rgb):
        Path(str(dst)[:-4] + '.skip').write_bytes(b'')
        return None
    big = enlarge(rgb, scale, work)
    blobs = []
    for level in mip_levels(big):
        h, w = level.shape[0] // 4 * 4, level.shape[1] // 4 * 4
        blobs.append((w, h, encode_bc6h(np.ascontiguousarray(level[:h, :w]))))
    write_dds_bc6h(dst, blobs)
    return rgb.shape[1], rgb.shape[0], big.shape[1], big.shape[0]


def pending(folder):
    out = []
    for src in sorted((Path(folder) / 'src').glob('*.dds')):
        if len(src.stem) == 16 and not (Path(folder) / src.name).exists() and not (Path(folder) / (src.stem + '.skip')).exists():
            out.append(src)
    return out


def generate(folder, scale=2, limit=0, report=print, cancel=None):
    """Enlarge every light map of folder/src that has no HD file yet. Returns (made, left as they are, failed)."""
    folder = Path(folder)
    todo = pending(folder)
    if limit:
        todo = todo[:limit]
    made = kept = failed = 0
    with tempfile.TemporaryDirectory(prefix='hdshadows-') as tmp:
        for n, src in enumerate(todo, 1):
            if cancel is not None and cancel.is_set():
                break
            try:
                done = build(src, folder / src.name, scale, Path(tmp))
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                failed += 1
                report(f'[{n}/{len(todo)}] {src.stem}: sin procesar ({error})')
                continue
            if done is None:
                kept += 1
            else:
                made += 1
            report(f'Sombras HD: {n}/{len(todo)} mapas de luz')
    return made, kept, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', type=Path, required=True, help='<GameData>/hdshadows')
    ap.add_argument('--scale', type=int, default=2, choices=(2, 3, 4))
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args(argv)
    ensure_esrgan()
    made, kept, failed = generate(a.dir, a.scale, a.limit, report=lambda text: print(text, flush=True))
    print(f'{made} HD light maps written, {kept} directional maps left as they are, {failed} failed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
