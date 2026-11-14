"""Package tracked source or an owner's private, self-contained Windows alpha.

Private output stays under ignored build/releases and is never a release asset.
No console keys, original packages, diagnostic logs or generated C are copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = '0.2-alpha'
sys.path.insert(0, str(ROOT))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tracked(root):
    return subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')[:-1]


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def source_files(target):
    for name in tracked(ROOT):
        source = ROOT / name
        if source.is_file():
            copy_file(source, target / name)
    upstream = ROOT / 'third_party/astral'
    for name in tracked(upstream):
        source = upstream / name
        if source.is_file():
            copy_file(source, target / 'third_party/astral' / name)


def private_files(target, profile, version):
    from newsnap.provenance import verify_import
    from newsnap.launcher_settings import ProfileLock, load_settings, save_settings
    verify_import(ROOT / 'build/extracted/updated')
    runtime = target / 'build/updated'
    names = ('newsnap.exe', 'SDL3.dll', 'libopus-0.dll', 'ac_xlate.exe', 'ac_xlate.id',
             'romfs-index.bin', 'shader-programs.bin', 'shader-answers.bin', 'pipeline-keys.bin')
    for name in names:
        copy_file(ROOT / 'build/updated' / name, runtime / name)
    ini = ROOT / 'build/updated/newsnap.ini'
    save_settings(runtime / ini.name, load_settings(ini))
    shutil.copytree(ROOT / 'build/extracted/updated/exefs', runtime / 'exefs')
    copy_file(ROOT / 'build/extracted/updated/romfs/romfs.bin', runtime / 'romfs/romfs.bin')
    # Library inputs are portable; driver-specific caches and prepared receipts are not.
    shutil.copytree(ROOT / 'build/shader-unpack/programs', target / 'build/shader-unpack/programs')
    with ProfileLock(profile):
        transaction = profile / 'save-tx'
        if any(transaction.glob('ready-*')) or any((transaction / name).exists() for name in ('new', 'old')):
            raise ValueError('A pending save commit must be recovered before packaging')
        for folder in ('save', 'save-backup', 'photos'):
            source = profile / folder
            if source.is_dir():
                if any(p.is_symlink() for p in source.rglob('*')):
                    raise ValueError('Profile links must be resolved before packaging')
                shutil.copytree(source, target / 'build/profile' / folder)
    (target / 'build/profile').mkdir(parents=True, exist_ok=True)
    # Bundle the existing official CPython installation and installed dependency
    # packages, preserving their licenses. No Python installation on the other PC.
    python = Path(sys.base_prefix)
    destination = target / 'python'
    destination.mkdir()
    for pattern in ('python*.exe', 'python*.dll', 'vcruntime*.dll', 'LICENSE.txt'):
        for file in python.glob(pattern):
            copy_file(file, destination / file.name)
    for folder in ('DLLs', 'tcl', 'Lib'):
        shutil.copytree(python / folder, destination / folder,
                        ignore=shutil.ignore_patterns('site-packages', '__pycache__', 'test', 'tests'))
    shutil.copytree(Path(sys.prefix) / 'Lib/site-packages', destination / 'Lib/site-packages',
                    ignore=shutil.ignore_patterns('__pycache__', 'pip', 'pip-*.dist-info'))
    (target / 'Iniciar NewSnap.cmd').write_text(
        '@echo off\ncd /d "%~dp0"\nstart "" "%~dp0python\\pythonw.exe" -E -s -m newsnap launcher\n',
        encoding='ascii')
    (target / 'Diagnostico NewSnap.cmd').write_text(
        '@echo off\ncd /d "%~dp0"\n"%~dp0python\\python.exe" -E -s -m newsnap launcher\npause\n',
        encoding='ascii')
    (target / 'LEEME-PORTABLE.txt').write_text(
        f'NewSnapRecomp {version} - paquete privado de MatyMeatBoy\n\n'
        'Extrae toda la carpeta y abre Iniciar NewSnap.cmd. No requiere instalar Python.\n'
        'Windows x64, CPU con AVX2 y GPU/controlador Vulkan. El segundo PC no esta verificado.\n'
        'La primera preparacion reconstruye shaders para su GPU y puede tardar.\n'
        'Tus datos estan en build/updated/exefs y romfs; guardados en build/profile.\n'
        'No contiene claves ni NSP originales. No publiques este paquete con datos del juego.\n'
        'Alpha: recorrido completo, puntuacion y persistencia de fotos aun sin verificar.\n',
        encoding='utf-8')


def package(private=False, profile=None):
    if private:
        raise ValueError('Private portable archives are discontinued; copy only your GameData folder')
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--ignore-submodules=none'], cwd=ROOT).returncode:
        raise ValueError('Commit or preserve tracked source changes before identifying a release revision')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    suffix = 'private-portable' if private else 'source'
    name = f'NewSnapRecomp-{VERSION}-{suffix}-{revision[:8]}'
    target = ROOT / 'build/releases' / name
    target.mkdir(parents=True, exist_ok=False)
    source_files(target)
    if private:
        private_files(target, Path(profile or ROOT / 'build/profile').resolve(), VERSION)
    files = {p.relative_to(target).as_posix(): {'size': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(target.rglob('*')) if p.is_file()}
    (target / 'MANIFEST.json').write_text(json.dumps({
        'version': VERSION, 'source_revision': revision, 'private_game_data': private,
        'files': files}, indent=2) + '\n', encoding='utf-8')
    archive = target.parent / (target.name + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as output:
        for file in sorted(target.rglob('*')):
            if file.is_file():
                output.write(file, Path(name) / file.relative_to(target))
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    print(json.dumps({'archive': str(archive), 'sha256': checksum, 'files': len(files)}, indent=2), flush=True)
    return target, archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private', action='store_true')
    parser.add_argument('--profile', type=Path)
    args = parser.parse_args()
    package(args.private, args.profile)
