"""Play a scripted input route on a copy of a runtime and a copy of a profile; nothing of the player's is touched.

    python -m tools.dev.route_run --out build/run1 --runtime <candidate dir> --data <GameData> --profile <profile copy>
        --route route.txt --seconds 110 [--save <save folder to seed>] [--cache <runtime dir with shader caches>]
        AC_FPS=144 AC_SHOTS=w14-108:0.5 NEWSNAP_PAD_TRACE=1 ...

`--out` must not exist; the runtime goes to <out>/runtime, the profile to <out>/profile (its saves, photos and caches
are left out; `--save` seeds one save folder), the log to <out>/run.log and AC_SHOTS pictures to <out>/shots. Route
lines are "<60 Hz tick> <button> [hold ticks]" (third_party/astral/runtime/input.c). The defaults are a hidden
1280x720 window, immediate present, 60 fps, no upscaler, no sound and no real controller; KEY=value arguments
override them. One GPU run at a time.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CACHES = ('shader-programs.bin', 'shader-answers.bin', 'pipeline-keys.bin', 'pipeline-cache.bin')


def main(argv):
    parser = argparse.ArgumentParser()
    for name in ('out', 'runtime', 'data', 'profile', 'route'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=110)
    parser.add_argument('--save', type=Path)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('settings', nargs='*')
    args = parser.parse_args(argv)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runtime, profile = out / 'runtime', out / 'profile'
    shutil.copytree(args.runtime, runtime)
    if args.cache:
        for name in CACHES:
            if (args.cache / name).is_file():
                shutil.copy2(args.cache / name, runtime / name)
    shutil.copytree(args.profile, profile,
                    ignore=shutil.ignore_patterns('save', 'save-tx', 'save-backup', 'temp', 'photos', 'cache'))
    if args.save:
        users = [p.name for p in (args.profile / 'save').iterdir() if p.is_dir()]
        if len(users) != 1:
            raise SystemExit('the profile must hold exactly one user save folder')
        shutil.copytree(args.save, profile / 'save' / users[0])
    route = out / 'route.txt'
    shutil.copy2(args.route, route)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('AC_', 'NEWSNAP_'))}
    env.update(AC_SNAP_RANDOM_RANGE='1', AC_GPU='vulkan', AC_INPUT='none', AC_INPUT_SCRIPT=str(route),
               AC_BACKGROUND_WINDOW='1', AC_FULLSCREEN='0', AC_WINDOW_SIZE='1280x720', AC_VOLUME='0',
               AC_RENDER_SCALE='100', AC_OPERATION_MODE='docked', AC_VK_PRESENT='immediate', AC_FPS='60',
               AC_MOTION='0', AC_UPSCALING='off', AC_REPLAY_ASYNC='1', AC_SHOTS_DIR=str(out / 'shots'))
    env.update(item.split('=', 1) for item in args.settings)
    command = [str(runtime / 'newsnap.exe'), '--exefs', str(args.data / 'exefs'), '--romfs', str(args.data / 'romfs'),
               '--profile', str(profile), '--seconds', str(args.seconds)]
    with (out / 'run.log').open('wb') as log:
        run = subprocess.run(command, cwd=runtime, env=env, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=args.seconds + 150)
    text = (out / 'run.log').read_text(encoding='utf-8', errors='replace')
    print(json.dumps({'exit_code': run.returncode, 'fatal': 'FATAL:' in text}))
    return run.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
