"""Build a Windows EXE launcher with the original icon; exclude all game data."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from newsnap.version import VERSION


def source_fingerprints(root=ROOT):
    files = []
    for pattern in ('newsnap/**/*.py', 'newsnap/overlays/*', 'assets/icons/*', 'assets/controllers/*', 'assets/launcher/*', 'assets/fonts/*', 'assets/game-fingerprints/*', 'profiles/*.json', 'third_party/recomp_achievements/**/*',
                    'tools/fetch_*.py', 'tools/package_build_kit.py', 'tools/triage_game_log.py',
                    'toolchain/hactool/*', 'toolchain/launcher-sdl/*'):
        files.extend(p for p in root.glob(pattern) if p.is_file())
    files.extend(root / name for name in ('tools/launcher_entry.py', 'tools/build_launcher.py',
                 'requirements-release.txt', 'requirements.txt', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
                 'third_party/astral/recomp/nso.py', 'assets/windows-version.txt', 'recomplauncher.json') if (root / name).is_file())
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}


def build():
    recipe = source_fingerprints()
    output = ROOT / 'build/launcher-dist'
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
               '--name', 'NewSnapLauncher', '--icon', str(ROOT / 'assets/icons/newsnap.ico'),
               '--version-file', str(ROOT / 'assets/windows-version.txt'),
               '--paths', str(ROOT), '--hidden-import', 'lz4.block', '--distpath', str(output),
               '--workpath', str(ROOT / 'build/launcher-pyinstaller'), '--specpath', str(ROOT / 'build'),
               str(ROOT / 'tools/launcher_entry.py')]
    subprocess.run(command, cwd=ROOT, check=True)
    application = output / 'NewSnapLauncher'
    # PKG-01: Tcl's time-zone database and Tcl/Tk's translated messages and demo images are about 770 small files
    # the launcher never reads (its texts are its own, it formats no dates through Tcl); the package lists shorter.
    for unused in ('_tcl_data/tzdata', '_tcl_data/msgs', '_tk_data/msgs', '_tk_data/images'):
        shutil.rmtree(application / '_internal' / unused, ignore_errors=True)
    for folder in ('assets/icons', 'assets/controllers', 'assets/launcher', 'assets/fonts', 'assets/game-fingerprints', 'licenses'):
        shutil.copytree(ROOT / folder, application / folder, dirs_exist_ok=True)
    # Older installed updaters accept only the curated Snap specifications here.
    # Native shader pins belong to the separate build kit, not the launcher.
    (application / 'profiles').mkdir(exist_ok=True)
    for spec in (ROOT / 'profiles').glob('snap-*.json'):
        shutil.copy2(spec, application / 'profiles' / spec.name)
    hactool = ROOT / 'toolchain/hactool/hactool.exe'   # NSP/XCI import from the launcher (home_ui.import_dump)
    if hactool.is_file():
        (application / 'tools').mkdir(parents=True, exist_ok=True)
        shutil.copy2(hactool, application / 'tools/hactool.exe')
        (application / 'licenses').mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'toolchain/hactool/LICENSE', application / 'licenses/hactool-LICENSE.txt')
    sdl = ROOT / 'toolchain/launcher-sdl/SDL3.dll'
    pin = json.loads((ROOT / 'assets/controllers/launcher-sdl.json').read_text(encoding='utf-8'))
    if not sdl.is_file() or hashlib.sha256(sdl.read_bytes()).hexdigest() != pin['sha256']:
        raise ValueError('Provision the exact pinned launcher SDL3 runtime before freezing')
    (application / 'tools/launcher-sdl').mkdir(parents=True, exist_ok=True)
    shutil.copy2(sdl, application / 'tools/launcher-sdl/SDL3.dll')
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'recomplauncher.json'):
        shutil.copy2(ROOT / name, application / name)
    for name in ('nso.py',):
        target = application / 'third_party/astral/recomp' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'third_party/astral/recomp' / name, target)
    shutil.copy2(ROOT / 'third_party/astral/LICENSE', application / 'third_party/astral/LICENSE')
    shutil.copy2(ROOT / 'third_party/astral/THIRD_PARTY_NOTICES.md', application / 'third_party/astral/THIRD_PARTY_NOTICES.md')
    (application / 'VERSION').write_text(VERSION + '\n', encoding='ascii')
    notices = application / 'licenses/runtime'
    notices.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(sys.base_prefix) / 'LICENSE.txt', notices / 'Python-LICENSE.txt')
    for name in ('PyInstaller', 'Pillow', 'cryptography', 'cffi', 'lz4', 'pycparser'):
        distribution = importlib.metadata.distribution(name)
        for item in distribution.files or ():
            if 'licenses' in Path(item).parts and distribution.locate_file(item).is_file():
                destination = notices / name / Path(*Path(item).parts[1:])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(distribution.locate_file(item), destination)
    if source_fingerprints() != recipe:
        raise ValueError('Launcher sources changed during freezing; rebuild the candidate')
    (application / 'launcher-build.json').write_text(json.dumps({'inputs': recipe,
        'python': sys.version, 'pyinstaller': importlib.metadata.version('PyInstaller')}, indent=2) + '\n', encoding='utf-8')
    print(application, flush=True)
    return application


if __name__ == '__main__':
    build()
