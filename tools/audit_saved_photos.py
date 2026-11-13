"""CPU-only audit of photographs stored in Snap save banks (FOTO-02).

Reads copies of bank 3 (full photographs) and bank 4 (thumbnails) strictly
read-only, reports every slot's container integrity and JPEG structure, decodes
each picture on the CPU and looks for black bands in the decoded pixels.

The purpose is to separate two failure classes:
  * bands present in the stored bytes  -> capture/readback/encoder path;
  * stored bytes clean                 -> preview/texture/presentation path.

Never point this at the owner's live profile while the game runs; use a copy
under build/.  The report contains hashes and measurements, never image data.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image

from newsnap.saves import SAVE_NAMES, _decrypt, iv_mask, shared_read

PHOTO_BANK, THUMB_BANK = 3, 4
BLACK_LEVEL = 24        # max channel value still counted as black (JPEG ringing)
BLACK_COVERAGE = 0.98   # share of a row/column that must be black
PROTECTED_PARTS = {'save', 'save-tx', 'save-backup', 'newsnapgamedata', 'gamedata'}
BLACK_BLOCK_SUSPECT = 0.01  # share of fully black 16x16 blocks worth a human look
SOF_MARKERS = {0xc0: 'baseline', 0xc1: 'extended', 0xc2: 'progressive'}


def jpeg_structure(data):
    """Walk JPEG segments without decoding; returns facts and problems."""
    info = {'bytes': len(data), 'problems': []}
    if data[:2] != b'\xff\xd8':
        info['problems'].append('sin SOI')
        return info
    pos, scans = 2, 0
    while pos + 4 <= len(data):
        if data[pos] != 0xff:
            info['problems'].append(f'marcador inesperado en {pos}')
            break
        marker = data[pos + 1]
        if marker == 0xd9:
            break
        length, = struct.unpack_from('>H', data, pos + 2)
        if length < 2 or pos + 2 + length > len(data):
            info['problems'].append(f'segmento {marker:#04x} truncado en {pos}')
            break
        body = data[pos + 4:pos + 2 + length]
        if marker in SOF_MARKERS or 0xc3 <= marker <= 0xcf and marker not in (0xc4, 0xc8, 0xcc):
            if len(body) < 6 or len(body) < 6 + 3 * body[5]:
                info['problems'].append(f'SOF demasiado corto en {pos}')
                pos += 2 + length
                continue
            precision, height, width, components = struct.unpack_from('>BHHB', body)
            info.update(sof=SOF_MARKERS.get(marker, f'{marker:#04x}'), precision=precision,
                        width=width, height=height,
                        sampling=[f'{body[7 + 3 * i] >> 4}x{body[7 + 3 * i] & 15}'
                                  for i in range(components)])
        elif marker == 0xdd:
            if len(body) < 2:
                info['problems'].append(f'DRI demasiado corto en {pos}')
            else:
                info['restart_interval'], = struct.unpack_from('>H', body)
        pos += 2 + length
        if marker == 0xda:
            scans += 1
            # Entropy-coded data: skip to the next real marker.
            expected_rst = 0
            while True:
                pos = data.find(b'\xff', pos)
                if pos < 0 or pos + 1 >= len(data):
                    info['problems'].append('datos de escaneo sin marcador final')
                    pos = len(data)
                    break
                following = data[pos + 1]
                if following == 0x00 or following == 0xff:
                    pos += 1 if following == 0xff else 2
                elif 0xd0 <= following <= 0xd7:
                    if following - 0xd0 != expected_rst:
                        info['problems'].append(f'RST fuera de secuencia en {pos}')
                    expected_rst = (following - 0xd0 + 1) % 8
                    pos += 2
                else:
                    break
    info['scans'] = scans
    if 'sof' not in info:
        info['problems'].append('sin SOF')
    if not scans:
        info['problems'].append('sin SOS')
    if data[-2:] != b'\xff\xd9':
        info['problems'].append('sin EOI final')
    return info


def _runs(mask):
    """Contiguous True runs of a 1-D mask as (start, length)."""
    padded = np.concatenate(([False], mask, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return [(int(a), int(b - a)) for a, b in zip(edges[::2], edges[1::2])]


def black_bands(pixels):
    """Find fully black rows/columns in an HxWx3 uint8 array.

    A run touching the border is 'edge' (could be legitimate letterboxing); a
    run with picture content on both sides is 'interior' and is the defect
    signature reported by the owner.  An entirely black picture is reported
    separately instead of as one huge band.
    """
    dark = pixels.max(axis=2) <= BLACK_LEVEL
    height, width = dark.shape
    # Share of whole 16x16 blocks that are black: catches partial-width stripes
    # (the owner's preview shows staggered half-rows, not full-width bands).
    blocks = dark[:height // 16 * 16, :width // 16 * 16].reshape(height // 16, 16, width // 16, 16)
    block_fraction = float(blocks.all(axis=(1, 3)).mean()) if blocks.size else 0.0
    result = {'black_fraction': round(float(dark.mean()), 5), 'all_black': bool(dark.all()),
              'black_block_fraction': round(block_fraction, 5),
              'black_blocks_suspect': block_fraction >= BLACK_BLOCK_SUSPECT,
              'rows': [], 'columns': []}
    if result['all_black']:
        return result
    for name, axis, extent in (('rows', 1, height), ('columns', 0, width)):
        for start, length in _runs(dark.mean(axis=axis) >= BLACK_COVERAGE):
            result[name].append({
                'start': start, 'length': length,
                'kind': 'edge' if start == 0 or start + length == extent else 'interior',
                'aligned8': start % 8 == 0 and length % 8 == 0,
                'aligned16': start % 16 == 0 and length % 16 == 0})
    return result


def has_bands(bands, interior_only=False):
    """Full-width/height bands, or (unless interior_only) suspect black blocks."""
    found = bands['rows'] + bands['columns']
    if not interior_only and bands.get('black_blocks_suspect') and not bands['all_black']:
        return True
    return any(not interior_only or band['kind'] == 'interior' for band in found)


def audit_jpeg(data):
    """Structure + CPU decode + band scan for one stored JPEG."""
    report = {'sha256': hashlib.sha256(data).hexdigest()}
    try:
        report['structure'] = jpeg_structure(data)
    except Exception as error:  # A malformed entry must never abort the bank.
        report['structure'] = {'bytes': len(data),
                               'problems': [f'analizador: {type(error).__name__}: {error}']}
    try:
        with Image.open(io.BytesIO(data)) as image:
            report['format'] = image.format
            pixels = np.asarray(image.convert('RGB'))
    except Exception as error:  # Pillow raises several unrelated types here.
        report['decode_error'] = f'{type(error).__name__}: {error}'
        return report, None
    report['width'], report['height'] = pixels.shape[1], pixels.shape[0]
    structure = report['structure']
    if (structure.get('width'), structure.get('height')) != (report['width'], report['height']):
        structure['problems'].append('dimensiones SOF distintas de las decodificadas')
    report['mean_rgb'] = [round(float(v), 2) for v in pixels.reshape(-1, 3).mean(axis=0)]
    report['bands'] = black_bands(pixels)
    return report, pixels


def bank_entries(path, file_index, key):
    """Yield one dict per slot; unlike saves.saved_jpegs, never stops at damage.

    Raises ValueError only when the container header itself is unusable.
    """
    seed = 0xb519fc35 + file_index
    with shared_read(path) as stream:
        size = stream.seek(0, 2)
        stream.seek(0)
        header = stream.read(48)
        if len(header) != 48:
            raise ValueError(f'Cabecera truncada: {path.name}')
        raw = _decrypt(header[:32], iv_mask(header[32:], seed), key)
        magic, packed, decoded, count, header_size, *_ = struct.unpack('<8I', raw)
        if (magic != 0xc63e569c or header_size != 48 or not 0 < count <= 4096
                or not 0 < decoded <= 16 << 20 or packed % 16 or packed < decoded + 48
                or packed > decoded + 63):
            raise ValueError(f'Cabecera de banco no válida (¿clave o índice erróneo?): {path.name}')
        yield {'header': {'packed': packed, 'decoded': decoded, 'count': count, 'file_bytes': size,
                          'expected_bytes': 48 + packed * count,
                          'size_ok': size == 48 + packed * count}}
        for slot in range(count):
            stream.seek(48 + packed * slot)
            block = stream.read(packed)
            entry = {'slot': slot}
            if len(block) != packed:
                entry['status'] = 'truncada'
                yield entry
                continue
            if block[:8] == bytes(8):
                entry['status'] = 'vacía'
                yield entry
                continue
            raw = _decrypt(block[16:], iv_mask(block[:16], seed + slot), key)
            adler, crc, entry_magic, length, duplicate, *_ = struct.unpack_from('<8I', raw)
            body = raw[32:32 + decoded]
            entry.update(magic_ok=entry_magic == 0x9b7a0b7c,
                         length_ok=length == decoded and duplicate == length,
                         adler_ok=zlib.adler32(body) == adler, crc_ok=zlib.crc32(body) == crc,
                         metadata_hex=body[:16].hex())
            intact = entry['magic_ok'] and entry['length_ok'] and entry['adler_ok'] and entry['crc_ok']
            if body[16:19] != b'\xff\xd8\xff':
                entry['status'] = 'no-foto' if intact else 'dañada'
                yield entry
                continue
            end = body.rfind(b'\xff\xd9', 19)
            if end < 0:
                entry['status'] = 'jpeg-sin-fin'
                yield entry
                continue
            entry['status'] = 'foto' if intact else 'foto-checksum-inválido'
            entry['padding_nonzero'] = any(body[end + 2:])
            entry['jpeg'] = body[16:end + 2]
            yield entry


def compare_pair(original, thumbnail):
    """Mean absolute luma difference between a thumbnail and its downscaled original.

    Orientative only.  Snap 2.0.1 thumbnails (240x200) are 6:5 crops of the 3:2
    photograph whose horizontal offset varies per photo (measured 120 px and
    192 px on the two local samples), so even a perfect pair differs by ~15-35
    luma on average here.  Use it to spot gross failures (a banded thumbnail of
    a clean photo pushes worst_row_mean far higher), never as a pass/fail gate.
    """
    height, width = thumbnail.shape[:2]
    source_height, source_width = original.shape[:2]
    crop_width = min(source_width, round(source_height * width / height))
    crop_height = min(source_height, round(source_width * height / width))
    left, top = (source_width - crop_width) // 2, (source_height - crop_height) // 2
    cropped = original[top:top + crop_height, left:left + crop_width]
    scaled = np.asarray(Image.fromarray(cropped).resize((width, height), Image.Resampling.BOX))
    luma = lambda rgb: rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    difference = np.abs(luma(scaled) - luma(thumbnail))
    return {'mean_abs_luma': round(float(difference.mean()), 2),
            'p99_abs_luma': round(float(np.percentile(difference, 99)), 2),
            'worst_row_mean': round(float(difference.mean(axis=1).max()), 2),
            'worst_row': int(difference.mean(axis=1).argmax())}


def find_banks(path):
    """Map a bank file, user folder or profile folder to [(file, index)]."""
    path = Path(path)
    wanted = {SAVE_NAMES[PHOTO_BANK]: PHOTO_BANK, SAVE_NAMES[THUMB_BANK]: THUMB_BANK}
    if path.is_file():
        if path.name not in wanted:
            raise ValueError(f'No es un banco de fotos o miniaturas: {path.name}')
        return [(path, wanted[path.name])]
    folders = [path]
    if (path / 'save').is_dir():
        folders = sorted(p for p in (path / 'save').iterdir() if p.is_dir() and not p.is_symlink())
    return [(folder / name, index) for folder in folders for name, index in wanted.items()
            if (folder / name).is_file() and not (folder / name).is_symlink()]


class UnsafeOutput(ValueError):
    """An output path would touch audited save data."""


def input_banks(sources):
    """Every bank file the given sources resolve to."""
    return [path for source in sources for path, _ in find_banks(source)]


def check_output(target, inputs):
    """Refuse outputs that are, alias, or live beside an input bank.

    Covers the same path, symlinks and hardlinks (os.path.samefile), any file
    inside a folder holding an input bank, and well-known save folder names.
    """
    target = Path(target)
    if target.is_symlink():
        raise UnsafeOutput(f'La salida es un enlace simbólico: {target}')
    resolved = target.resolve()
    if {part.lower() for part in resolved.parts} & PROTECTED_PARTS:
        raise UnsafeOutput(f'No se escribe dentro de datos de guardado: {target}')
    if resolved.name in SAVE_NAMES:
        raise UnsafeOutput(f'La salida tiene nombre de archivo de guardado: {target}')
    for bank in inputs:
        bank_resolved = Path(bank).resolve()
        if resolved == bank_resolved or (target.exists() and os.path.samefile(target, bank)):
            raise UnsafeOutput(f'La salida coincide con un banco de entrada: {target}')
        if resolved.is_relative_to(bank_resolved.parent):
            raise UnsafeOutput(f'La salida está en la carpeta de un banco de entrada: {target}')


def safe_write(target, data, inputs):
    """Write bytes after re-checking the target against every input bank."""
    target = Path(target)
    check_output(target, inputs)
    target.parent.mkdir(parents=True, exist_ok=True)
    check_output(target, inputs)  # the parent may have been a link until now
    target.write_bytes(data)


def _digest(path):
    digest = hashlib.sha256()
    with shared_read(path) as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def audit(paths, key, export_dir=None):
    """Audit banks; returns a JSON-serialisable report."""
    report = {'thresholds': {'black_level': BLACK_LEVEL, 'black_coverage': BLACK_COVERAGE},
              'banks': [], 'pairs': []}
    decoded = {}  # (folder, slot) -> {index: pixels}
    inputs = input_banks(paths)
    if export_dir:
        check_output(Path(export_dir) / 'x.jpg', inputs)
    for source in paths:
        for path, index in find_banks(source):
            before = _digest(path)
            bank = {'path': str(path), 'index': index, 'sha256': before,
                    'kind': 'fotos' if index == PHOTO_BANK else 'miniaturas', 'slots': []}
            try:
                for entry in bank_entries(path, index, key):
                    if 'header' in entry:
                        bank['header'] = entry['header']
                        continue
                    data = entry.pop('jpeg', None)
                    if data is not None:
                        try:
                            entry['jpeg'], pixels = audit_jpeg(data)
                        except Exception as error:  # keep auditing the other slots
                            entry['jpeg'] = {'sha256': hashlib.sha256(data).hexdigest(),
                                             'structure': {'bytes': len(data), 'problems': []},
                                             'decode_error': f'{type(error).__name__}: {error}'}
                            pixels = None
                        if pixels is not None:
                            decoded.setdefault((path.parent, entry['slot']), {})[index] = pixels
                            if export_dir and has_bands(entry['jpeg']['bands']):
                                name = f"{bank['kind']}-{entry['slot']:04d}-{entry['jpeg']['sha256'][:12]}.jpg"
                                safe_write(Path(export_dir) / name, data, inputs)
                    if entry['status'] != 'vacía':
                        bank['slots'].append(entry)
            except UnsafeOutput:
                raise
            except Exception as error:
                bank['error'] = f'{type(error).__name__}: {error}'
            bank['unchanged_after_read'] = _digest(path) == before
            report['banks'].append(bank)
    for (folder, slot), images in sorted(decoded.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        if PHOTO_BANK in images and THUMB_BANK in images:
            report['pairs'].append({'folder': str(folder), 'slot': slot,
                                    **compare_pair(images[PHOTO_BANK], images[THUMB_BANK])})
    report['summary'] = summarise(report)
    return report


def summarise(report):
    summary = {}
    for kind in ('fotos', 'miniaturas'):
        slots = [slot for bank in report['banks'] if bank['kind'] == kind for slot in bank['slots']]
        photos = [slot for slot in slots if 'jpeg' in slot]
        ok = [slot['jpeg'] for slot in photos if 'bands' in slot['jpeg']]
        summary[kind] = {
            'entradas': len(slots), 'jpeg': len(photos),
            'checksum_inválido': sum(slot['status'] in ('foto-checksum-inválido', 'dañada') for slot in slots),
            'decodificación_fallida': sum('decode_error' in slot['jpeg'] for slot in photos),
            'estructura_con_problemas': sum(bool(slot['jpeg']['structure']['problems']) for slot in photos),
            'otras_no_válidas': sum(slot['status'] in ('truncada', 'jpeg-sin-fin') for slot in slots),
            'todo_negro': sum(item['bands']['all_black'] for item in ok),
            'con_bandas': sum(has_bands(item['bands']) for item in ok),
            'con_bloques_negros': sum(item['bands']['black_blocks_suspect'] for item in ok),
            'max_bloques_negros': max((item['bands']['black_block_fraction'] for item in ok), default=0.0),
            'con_bandas_interiores': sum(has_bands(item['bands'], True) for item in ok),
            'dimensiones': sorted({f"{item['width']}x{item['height']}" for item in ok})}
    photos, thumbs = summary['fotos'], summary['miniaturas']
    issues = []
    for bank in report['banks']:
        name = f"{bank['kind']} {bank['path']}"
        if 'error' in bank:
            issues.append(f"{name}: {bank['error']}")
        elif not bank.get('header', {}).get('size_ok', False):
            issues.append(f'{name}: tamaño de archivo incoherente con la cabecera')
        if not bank['unchanged_after_read']:
            issues.append(f'{name}: el archivo cambió durante la lectura')
        for slot in bank['slots']:
            jpeg = slot.get('jpeg', {})
            if slot['status'] not in ('foto', 'no-foto'):
                issues.append(f"{name} pos. {slot['slot']}: {slot['status']}")
            if 'decode_error' in jpeg:
                issues.append(f"{name} pos. {slot['slot']}: no decodifica ({jpeg['decode_error']})")
            elif jpeg.get('structure', {}).get('problems'):
                issues.append(f"{name} pos. {slot['slot']}: {'; '.join(jpeg['structure']['problems'])}")
    if not report['banks']:
        issues.append('no se encontró ningún banco de fotos o miniaturas')
    summary['incidencias'] = issues
    summary['evidencia_completa'] = not issues
    if photos['con_bandas'] or photos['todo_negro']:
        verdict = 'bandas-en-bytes-de-foto'
    elif thumbs['con_bandas'] or thumbs['todo_negro']:
        verdict = 'bandas-solo-en-miniaturas-guardadas'
    elif issues:
        # Never call bytes clean when something could not be read or decoded.
        verdict = 'incompleto-o-dañado'
    elif photos['jpeg'] or thumbs['jpeg']:
        verdict = 'bytes-limpios'
    else:
        verdict = 'sin-fotos'
    summary['veredicto'] = verdict
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('sources', nargs='+', type=Path,
                        help='copia de perfil, carpeta de usuario o archivo de banco')
    parser.add_argument('--out', type=Path, required=True, help='informe JSON (fuera del guardado)')
    parser.add_argument('--export-flagged', type=Path,
                        help='carpeta local (p. ej. build/...) para copiar los JPEG con bandas')
    args = parser.parse_args(argv)
    try:
        inputs = input_banks(args.sources)
        check_output(args.out, inputs)
        if args.export_flagged:
            check_output(args.export_flagged / 'x.jpg', inputs)
            if args.out.resolve().is_relative_to(args.export_flagged.resolve()):
                raise UnsafeOutput('El informe no puede estar dentro de la carpeta de exportación')
    except ValueError as error:
        parser.error(str(error))
    from newsnap.saves import local_save_key
    report = audit(args.sources, local_save_key(), args.export_flagged)
    safe_write(args.out, json.dumps(report, ensure_ascii=False, indent=1).encode('utf-8'), inputs)
    print(json.dumps(report['summary'], ensure_ascii=False, indent=1))
    # 0 only for a complete, clean audit; 1 bands found; 2 incomplete evidence.
    verdict = report['summary']['veredicto']
    return 0 if verdict in ('bytes-limpios', 'sin-fotos') else 2 if verdict == 'incompleto-o-dañado' else 1


if __name__ == '__main__':
    raise SystemExit(main())
