"""Opt-in, windowless RecompLauncher adapter; normal launcher startup is unchanged."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from . import launcher_settings as settings
from .paths import runtime_dir, select_data_dir


def handles(argv):
    return any(arg in ('--recomplauncher-prepare', '--recomplauncher-play') for arg in argv)


def arguments(argv):
    parser = argparse.ArgumentParser(description='NewSnapRecomp RecompLauncher integration')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--recomplauncher-prepare', action='store_true')
    mode.add_argument('--recomplauncher-play', action='store_true')
    parser.add_argument('--game', type=Path, help='Imported GameData folder or your base NSP/NSZ/XCI/XCZ')
    parser.add_argument('--update', type=Path, help='Your 2.0.1 update NSP/NSZ')
    parser.add_argument('--keys', type=Path, help='Your own prod.keys file; never copied into the release')
    parser.add_argument('--set', action='append', default=[], metavar='KEY=VALUE')
    args = parser.parse_args(argv)
    values = {}
    for option in args.set:
        key, separator, value = option.partition('=')
        if not separator:
            parser.error('--set requires KEY=VALUE')
        values[key] = value
    try:
        args.settings = settings.validate_settings(values)
    except ValueError as error:
        parser.error(str(error))
    return args


def offline_kit(root):
    """The public release bundles the exact kit. Never silently acquire another online."""
    from .build_kit import ensure_build_kit, _identity, _bundled_archive
    revision, _ = _identity(root)
    if not os.environ.get('NEWSNAP_BUILD_KIT') and _bundled_archive(root, revision, None) is None:
        raise ValueError('Extract the complete release package, including its build kit.')
    return Path(ensure_build_kit(root))


def prepare(root, args):
    from . import home_state, maintenance
    if args.game is not None:
        if args.game.is_dir():
            select_data_dir(root, args.game)
        else:
            if not args.update or not args.keys or not all(p.is_file() for p in (args.game, args.update, args.keys)):
                raise ValueError('A packaged base game needs --update (2.0.1) and --keys (your prod.keys).')
            kit = offline_kit(root)
            hactool = next((p for p in (root / 'tools/hactool.exe', root / 'toolchain/hactool/hactool.exe')
                            if p.is_file()), None)
            if hactool is None:
                raise ValueError('The complete release package must include hactool.exe.')
            work = root / 'GameData-import'
            emit(.1, 'Importing your game and 2.0.1 update')
            maintenance.run_build_command([kit / 'python/python.exe', '-B', '-E', '-s', '-m', 'newsnap',
                'import', '--base', args.game, '--update', args.update, '--keys', args.keys,
                '--work', work, '--hactool', hactool], kit / 'source', root / 'logs/recomplauncher-import.log')
            select_data_dir(root, work / 'updated')
    emit(.35, 'Verifying your game data')
    with settings.ProfileLock(settings.load_profile(root)):
        home_state.verify(root)
    if maintenance.assess_runtime(root)['needs_rebuild']:
        emit(.45, 'Building the game locally with the included tools')
        maintenance.rebuild_runtime(root, offline_kit(root))
    settings.validate_runtime_data(root)


def game_environment(root, overrides):
    env = settings.game_environment(root=root)
    current = settings.load_settings(runtime_dir(root) / 'newsnap.ini')
    combined = {**current, **overrides}
    settings.validate_video_combination(combined)
    values = dict(overrides)
    mode = os.environ.get('RECOMPLAUNCHER_MODE')
    if mode in ('bigpicture', 'desktop'):
        values.setdefault('fullscreen', '1' if mode == 'bigpicture' else '0')
    pad = os.environ.get('RECOMPLAUNCHER_PAD')
    if pad in ('xbox', 'playstation') and combined.get('pad_layout', 'auto') == 'auto':
        values.setdefault('pad_layout', pad)
    env.update({'AC_' + key.upper(): value for key, value in values.items()})
    env['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '0'
    return env


def play(root, overrides):
    from .maintenance import assess_runtime
    if assess_runtime(root)['needs_rebuild']:
        # Release updates keep imported data. Rebuild from it with this release's
        # bundled kit, without asking the player for their original containers again.
        prepare(root, argparse.Namespace(game=None))
    profile = settings.load_profile(root)
    with settings.ProfileLock(profile):
        if assess_runtime(root)['needs_rebuild']:
            raise ValueError('Run RecompLauncher setup to build or update the game first.')
        settings.validate_runtime_data(root)
        env = game_environment(root, overrides)
        logs = root / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        session = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]

        def attempt(number):
            from .startup_assets import prepare_hd_shadows
            if 'hd_shadows' not in overrides:
                env.pop('AC_HD_SHADOWS', None)
            prepare_hd_shadows(root, env, report=lambda text: emit(0.95, text),
                               explicit=overrides.get('hd_shadows') == '1')
            path = logs / f'recomplauncher-game-{session}-{number:03d}.log'
            with path.open('x', encoding='utf-8') as log:
                process = subprocess.Popen(settings.game_command(root, profile), cwd=root, env=env,
                    stdout=log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                return process.wait()

        return settings.supervise_game(attempt)


def emit(ratio, text):
    if sys.stdout is not None:
        print(f'progress {ratio:g} {text}', flush=True)


def _attach_streams():
    # A PyInstaller windowed executable starts with sys.stdout/stderr=None even when
    # its caller supplies pipes. Adopt duplicate inherited handles; never open a console.
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.DuplicateHandle.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.DuplicateHandle.restype = wintypes.BOOL
    for name, identifier in (('stdout', -11), ('stderr', -12)):
        if getattr(sys, name) is not None:
            continue
        handle = kernel.GetStdHandle(identifier & 0xffffffff)
        duplicate = wintypes.HANDLE()
        process = kernel.GetCurrentProcess()
        if handle and kernel.DuplicateHandle(process, handle, process, ctypes.byref(duplicate), 0, False, 2):
            fd = msvcrt.open_osfhandle(duplicate.value, os.O_WRONLY)
            setattr(sys, name, os.fdopen(fd, 'w', encoding='utf-8', buffering=1))


def main(argv, root):
    _attach_streams()
    try:
        args = arguments(argv)
    except SystemExit as error:
        return error.code
    root = Path(root).resolve()
    (root / 'logs').mkdir(parents=True, exist_ok=True)
    try:
        if args.recomplauncher_prepare:
            (root / 'recomplauncher-ready.json').unlink(missing_ok=True)
            emit(0, 'Checking setup inputs')
            prepare(root, args)
            from .version import VERSION
            settings._atomic_write(root / 'recomplauncher-ready.json',
                (json.dumps({'version': VERSION}) + '\n').encode('utf-8'))
            emit(1, 'Ready to play')
            return 0
        return play(root, args.settings)
    except (OSError, ValueError, RuntimeError) as error:
        message = str(error).replace('\n', ' ').replace('\r', ' ')
        with (root / 'logs/recomplauncher-setup.log').open('a', encoding='utf-8') as log:
            log.write(message + '\n')
        if sys.stderr is not None:
            print(message, file=sys.stderr, flush=True)
        return 2
