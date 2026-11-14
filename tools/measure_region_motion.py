"""Sub-pixel motion of picture regions between consecutive frames (HEAD-INTRO).

Given a folder of consecutive frame pictures (the runtime's flight-recorder
dump, AC_FLIGHT=1) and named rectangles, measures how far the content of each
rectangle moves from one present to the next and how regular those steps are.
It separates three things a "stutter" report can mean:

  * late frames              -> the dump's interval column, not this tool;
  * the whole picture uneven -> every region irregular, the background too;
  * one part uneven          -> that region irregular while the background,
                                which only shows the camera, stays smooth.

Read-only; needs numpy and Pillow.  Frames are data from a local run and stay
in build/.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image

FRAME_NAME = re.compile(r'^f(\d+)\.png$')


def shift(image, dx, dy):
    """image sampled at (x + dx, y + dy), bilinear, edges clamped."""
    height, width = image.shape
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
    xs, ys = np.clip(xs + dx, 0, width - 1), np.clip(ys + dy, 0, height - 1)
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    x1, y1 = np.minimum(x0 + 1, width - 1), np.minimum(y0 + 1, height - 1)
    fx, fy = xs - x0, ys - y0
    return (image[y0, x0] * (1 - fx) * (1 - fy) + image[y0, x1] * fx * (1 - fy) +
            image[y1, x0] * (1 - fx) * fy + image[y1, x1] * fx * fy)


def displacement(previous, current, box, pad=6, iterations=20):
    """(dx, dy, residual): how the content of box moved from previous to current.

    Iterated Lucas-Kanade with warping; valid for motions of a few pixels on
    textured content.  residual is the mean absolute difference left after the
    alignment (grey levels): large values mean the region changed, not moved.
    """
    x0, y0, x1, y1 = box
    height, width = previous.shape
    if x0 - pad < 0 or y0 - pad < 0 or x1 + pad > width or y1 + pad > height or x1 <= x0 or y1 <= y0:
        raise ValueError(f'Region {box} does not fit in a {width}x{height} frame with a {pad}-pixel margin')
    a = previous[y0 - pad:y1 + pad, x0 - pad:x1 + pad]
    b = current[y0 - pad:y1 + pad, x0 - pad:x1 + pad]
    gy, gx = np.gradient(a)
    inner = (slice(pad, -pad), slice(pad, -pad))
    design = np.stack([gx[inner].ravel(), gy[inner].ravel()], axis=1)
    normal = design.T @ design + np.eye(2) * 1e-6
    dx = dy = 0.0
    for _ in range(iterations):
        error = (shift(b, dx, dy)[inner] - a[inner]).ravel()
        step = np.linalg.solve(normal, design.T @ error)
        dx -= step[0]
        dy -= step[1]
        if abs(step[0]) + abs(step[1]) < 1e-4:
            break
    residual = float(np.abs(shift(b, dx, dy)[inner] - a[inner]).mean())
    return float(dx), float(dy), residual


def regularity(dx, dy, window=5, frame_numbers=None):
    """How uneven a series of per-frame steps is.

    irregularity: RMS of the steps' deviation from their running mean over
    `window` frames, relative to the mean step length.  alternation: the part of
    that deviation that flips sign every frame (a component updated at half the
    frame rate), relative to the mean step length. Frame numbers identify the
    original present of each step; gaps split the running mean into independent
    segments and never change the even/odd phase of later frames.
    """
    dx, dy = np.asarray(dx, dtype=np.float64), np.asarray(dy, dtype=np.float64)
    frame_numbers = np.arange(len(dx)) if frame_numbers is None else np.asarray(frame_numbers)
    if dx.ndim != 1 or dy.shape != dx.shape or frame_numbers.shape != dx.shape:
        raise ValueError('Steps and frame numbers must be equally sized one-dimensional arrays')
    if len(frame_numbers) and (not np.issubdtype(frame_numbers.dtype, np.integer) or
                               np.any(frame_numbers[1:] <= frame_numbers[:-1])):
        raise ValueError('Frame numbers must be strictly increasing integers')
    length = float(np.hypot(dx, dy).mean()) if len(dx) else 0.0
    cuts = np.flatnonzero(np.diff(frame_numbers) != 1) + 1
    segments = np.split(np.arange(len(dx)), cuts) if len(dx) else []
    result = {'frames': int(len(dx)), 'segments': len(segments), 'analyzed_pairs': 0,
              'mean_step': round(length, 4), 'irregularity': None, 'alternation': None}
    if length == 0.0:
        return result
    half = window // 2 + 1
    kernel = np.ones(window) / window
    parts, scored_frames = [], []
    for segment in segments:
        if len(segment) < window + 4:
            continue
        parts.append([(axis[segment] - np.convolve(axis[segment], kernel, mode='same'))[half:-half]
                      for axis in (dx, dy)])
        scored_frames.append(frame_numbers[segment][half:-half])
    if not parts:
        return result
    deviation = [np.concatenate([part[axis] for part in parts]) for axis in (0, 1)]
    rms = float(np.sqrt(sum((d * d).mean() for d in deviation)))
    sign = np.where(np.concatenate(scored_frames) % 2 == 0, 1.0, -1.0)
    alternating = float(np.hypot(*((d * sign).mean() for d in deviation)))
    result.update(analyzed_pairs=len(deviation[0]), irregularity=round(rms / length, 4),
                  alternation=round(alternating / length, 4))
    return result


def frame_files(folder):
    frames = {}
    for path in Path(folder).iterdir():
        if match := FRAME_NAME.match(path.name):
            frames[int(match.group(1))] = path
    if not frames:
        raise ValueError(f'No f<number>.png frames in {folder}')
    return frames


def intervals(folder):
    """Present intervals (ms) from a flight dump's frames.tsv, when there is one."""
    path = Path(folder) / 'frames.tsv'
    result = {}
    if path.is_file():
        with path.open(encoding='utf-8', errors='replace') as stream:
            for row in csv.reader(stream, delimiter='\t'):
                if len(row) > 2 and row[0].isdigit():
                    result[int(row[0])] = float(row[2])
    return result


def measure(folder, boxes, first=None, last=None, residual_limit=15.0):
    """Per-frame displacement and regularity of every named box over consecutive frames."""
    files = frame_files(folder)
    first = min(files) if first is None else first
    last = max(files) if last is None else last
    timing = intervals(folder)
    rows, previous, previous_number = [], None, None
    for number in range(first, last + 1):
        if number not in files:
            previous = None   # a gap: never measure across a missing frame
            continue
        current = np.asarray(Image.open(files[number]).convert('L')).astype(np.float64)
        if previous is not None and previous_number == number - 1:
            row = {'frame': number, 'interval_ms': timing.get(number)}
            for name, box in boxes.items():
                dx, dy, residual = displacement(previous, current, box)
                row[name] = {'dx': round(dx, 4), 'dy': round(dy, 4), 'residual': round(residual, 2)}
            rows.append(row)
        previous, previous_number = current, number
    summary = {}
    for name in boxes:
        usable = [row for row in rows if row[name]['residual'] <= residual_limit]
        summary[name] = regularity([row[name]['dx'] for row in usable], [row[name]['dy'] for row in usable],
                                   frame_numbers=[row['frame'] for row in usable])
        summary[name]['discarded'] = len(rows) - len(usable)
    present = [row['interval_ms'] for row in rows if row['interval_ms'] is not None]
    if present:
        summary['present_interval_ms'] = {'mean': round(float(np.mean(present)), 3), 'std': round(float(np.std(present)), 3),
                                          'max': round(float(np.max(present)), 3)}
    return {'first': first, 'last': last, 'measured_pairs': len(rows), 'rows': rows, 'summary': summary}


def parse_box(text):
    name, _, values = text.partition(':')
    numbers = [int(value) for value in values.split(',')] if values else []
    if not name or len(numbers) != 4:
        raise argparse.ArgumentTypeError('región: nombre:x0,y0,x1,y1')
    return name, numbers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('frames', type=Path, help='carpeta con f<número>.png consecutivos (volcado AC_FLIGHT)')
    parser.add_argument('--box', action='append', required=True, type=parse_box, help='nombre:x0,y0,x1,y1')
    parser.add_argument('--first', type=int)
    parser.add_argument('--last', type=int)
    parser.add_argument('--out', type=Path, help='JSON con las series completas')
    args = parser.parse_args(argv)
    try:
        report = measure(args.frames, dict(args.box), args.first, args.last)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.out:
        if args.out.resolve().parent == args.frames.resolve():
            parser.error('El informe no se escribe dentro de la carpeta de fotogramas')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=1), encoding='utf-8')
    sys.stdout.write(json.dumps({key: report[key] for key in ('first', 'last', 'measured_pairs', 'summary')},
                                ensure_ascii=False, indent=1) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
