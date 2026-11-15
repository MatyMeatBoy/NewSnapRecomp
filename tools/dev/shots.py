"""Compare AC_SHOTS series of two runs of the same route (tools/dev/route_run.py). Needs Pillow and numpy.

    python -m tools.dev.shots lead <reference run> <run>...     # for each shot of a run, how many shots ahead of the
                                                                # reference the closest reference picture is
    python -m tools.dev.shots sheet <run> [first] [count] [columns]   # contact sheet <run>/sheet.jpg
    python -m tools.dev.shots pages <run>...                    # which scripted presses changed the dialogue page
                                                                # (needs NEWSNAP_PAD_TRACE=1 in the run)

`lead` is how INPUT-HZ-01 was reproduced: the same presses at 60 and 144 fps, the 144 fps run getting ahead.
`pages` prints one item per press: "A" a state change was raised, "p" the page left, "n"/"N" a new page or scene.
"""
import os
import re
import sys


def series(run):
    import numpy as np
    from PIL import Image
    folder = os.path.join(run, 'shots')
    return [np.asarray(Image.open(os.path.join(folder, name)).convert('L').resize((96, 54)), dtype=float)
            for name in sorted(os.listdir(folder))]


def lead(reference, runs):
    import numpy as np
    base = series(reference)
    for run in runs:
        ahead = [int(np.argmin([np.abs(shot - other).mean() for other in base])) - index
                 for index, shot in enumerate(series(run))]
        print(run, ' '.join(str(value) for value in ahead))


def sheet(run, first=0, count=192, columns=12):
    from PIL import Image
    folder = os.path.join(run, 'shots')
    names = sorted(os.listdir(folder))[first:first + count]
    rows = (len(names) + columns - 1) // columns
    picture = Image.new('RGB', (240 * columns, 135 * rows))
    for index, name in enumerate(names):
        picture.paste(Image.open(os.path.join(folder, name)).resize((240, 135)),
                      ((index % columns) * 240, (index // columns) * 135))
    picture.save(os.path.join(run, 'sheet.jpg'), quality=85)


def pages(runs):
    for run in runs:
        presses, current = [], None
        with open(os.path.join(run, 'run.log'), encoding='utf-8', errors='replace') as log:
            for line in log:
                match = re.search(r'script frame \d+ tick (\d+)', line)
                if match:
                    if current:
                        presses.append(current)
                    current = [int(match.group(1)), '']
                match = re.search(r'snap_event: frame \d+ object \w+ event (\d+)', line)
                if match and current:
                    current[1] += {16: 'A', 21: 'p', 1: 'N', 5: 'n'}.get(int(match.group(1)), '')
        if current:
            presses.append(current)
        print(run, ' '.join(f'{tick}:{what or "."}' for tick, what in presses))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == 'lead':
        lead(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == 'sheet':
        sheet(sys.argv[2], *(int(value) for value in sys.argv[3:6]))
    elif sys.argv[1] == 'pages':
        pages(sys.argv[2:])
    else:
        sys.exit(__doc__)
