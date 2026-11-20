"""Close a standalone launcher release. Owner GameData is always excluded."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import stat
import subprocess
import zipfile

from tools.build_launcher import ROOT, source_fingerprints
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES
from newsnap.upstream import COMMIT
from newsnap import build_kit, updater

MAX_PACKAGE_BYTES = 1 << 30
MAX_PACKAGE_EXPANDED_BYTES = 2 << 30


def _public_kit_member(name):
    """Same public scope as package_build_kit, applied before reading members."""
    path = updater._relative(name)
    parts = tuple(part.casefold() for part in path.parts)
    if (any(part in ('gamedata', 'newsnapgamedata', 'exefs', 'romfs') for part in parts)
            or parts[0] == 'source' and any(part in ('generated', 'extracted', 'profile') for part in parts)
            or path.suffix.casefold() in ('.nsp', '.nsz', '.xci', '.xcz', '.nca', '.nso', '.npdm', '.keys', '.drp', '.nushdb', '.bin')
            or path.name.casefold() in ('main', 'sdk', 'newsnap.exe', 'romfs.bin', '.env', 'credentials')):
        raise ValueError('Private content in bundled build kit')
    return path


def closed_build_kit(revision):
    """Verify the closed public ZIP in place, without extraction or execution."""
    name = f'NewSnapBuildKit-{VERSION}-{revision[:8]}.zip'
    archive = ROOT / 'build/releases' / name
    sidecar = archive.with_suffix('.zip.sha256')
    for path in (archive, sidecar):
        updater._no_links(path)
        if not path.is_file():
            raise ValueError('Close the matching public build kit before packaging Windows')
    if archive.stat().st_size > MAX_PACKAGE_BYTES or sidecar.stat().st_size > 4096:
        raise ValueError('Bundled build kit or checksum exceeds package limit')
    fields = sidecar.read_text(encoding='ascii').strip().split()
    if (len(fields) != 2 or not re.fullmatch('[0-9a-fA-F]{64}', fields[0])
            or fields[1] != name or digest(archive) != fields[0].lower()):
        raise ValueError('Closed build-kit ZIP checksum differs')
    pins = {archive.name: fields[0].lower(), sidecar.name: digest(sidecar)}
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if not members or len(members) > build_kit.MAX_FILES * 2:
            raise ValueError('Invalid build-kit member count')
        inventory, seen, total = {}, set(), 0
        for member in members:
            relative = updater._relative(member.filename.rstrip('/') if member.is_dir() else member.filename)
            if relative.parts[0] != name[:-4] or len(relative.parts) < (1 if member.is_dir() else 2):
                raise ValueError('Build kit must have its canonical single root')
            key = relative.as_posix().casefold()
            mode = member.external_attr >> 16
            if (key in seen or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or member.external_attr & 0x400 or member.flag_bits & 1):
                raise ValueError('Build-kit duplicate, link, special or encrypted member')
            seen.add(key)
            total += member.file_size
            if total > build_kit.MAX_EXPANDED_BYTES:
                raise ValueError('Expanded build kit exceeds limit')
            if not member.is_dir():
                name_in_kit = '/'.join(relative.parts[1:])
                _public_kit_member(name_in_kit)
                inventory[name_in_kit] = member
        entry = inventory.get('build-kit.json')
        if entry is None or entry.file_size > build_kit.MAX_MANIFEST_BYTES:
            raise ValueError('Build kit needs a bounded manifest')
        manifest = json.loads(source.read(entry))
        expected = build_kit._inventory(manifest, revision)
        if (manifest.get('format') != 1 or manifest.get('runtime_version') != VERSION
                or manifest.get('runtime_api') != RUNTIME_API or manifest.get('donor_commit') != COMMIT
                or set(manifest.get('capabilities', [])) != set(RUNTIME_CAPABILITIES)):
            raise ValueError('Build kit differs from the Windows runtime recipe')
        required = {'python/python.exe', 'source/newsnap/maintenance.py', 'source/newsnap/build.py',
                    'source/third_party/astral/tools/build_game.py', 'sdk/llvm/bin/clang.exe', 'sdk/bin/ninja.exe'}
        if not required <= set(expected) or set(inventory) != set(expected) | {'build-kit.json'}:
            raise ValueError('Build-kit ZIP differs from its complete inventory')
        for relative, checksum in expected.items():
            with source.open(inventory[relative]) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != checksum:
                    raise ValueError('Build-kit member checksum differs: ' + relative)
    if any(digest(path) != pins[path.name] for path in (archive, sidecar)):
        raise ValueError('Closed build-kit asset changed during verification')
    return archive, sidecar, pins


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_public_tree(folder):
    forbidden = {'.nsp', '.nsz', '.xci', '.nca', '.keys', '.nso', '.npdm', '.drp', '.nushdb', '.bin'}
    for file in folder.rglob('*'):
        if file.is_symlink() or (hasattr(file, 'is_junction') and file.is_junction()):
            raise ValueError('Release links are not permitted')
        if any(part.lower() in ('gamedata', 'newsnapgamedata') for part in file.relative_to(folder).parts):
            raise ValueError('Owner data cannot be a public release asset')
        if file.suffix.lower() in forbidden or file.name.lower() in ('main', 'sdk', 'newsnap.exe', 'romfs.bin', 'romfs-index.bin'):
            raise ValueError('Game-derived or private content in launcher candidate')


def package():
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--ignore-submodules=none'], cwd=ROOT).returncode:
        raise ValueError('Commit source changes before closing the release')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    candidate = ROOT / 'build/launcher-dist/NewSnapLauncher'
    receipt = json.loads((candidate / 'launcher-build.json').read_text(encoding='utf-8'))
    if receipt['inputs'] != source_fingerprints():
        raise ValueError('Stale launcher executable; rebuild before packaging')
    verify_public_tree(candidate)
    kit, kit_checksum, kit_pins = closed_build_kit(revision)
    name = f'NewSnapRecomp-{VERSION}-windows-x64-{revision[:8]}'
    destination = ROOT / 'build/releases' / name
    shutil.copytree(candidate, destination)
    bundled = destination / 'build-kits'
    bundled.mkdir(exist_ok=False)
    for source in (kit, kit_checksum):
        target = bundled / source.name
        shutil.copy2(source, target)
        if digest(target) != kit_pins[source.name]:
            raise ValueError('Build-kit changed while copying the closed asset')
    (destination / 'LEEME.txt').write_text(
        f'NewSnapRecomp {VERSION} - MatyMeatBoy\n\n'
        'Extrae toda esta carpeta. Copia tu carpeta GameData junto a NewSnapLauncher.exe.\n'
        'Abre NewSnapLauncher.exe. Conserva _internal y las otras carpetas de la release.\n'
        'No requiere instalar Python. GameData no se incluye en GitHub.\n\n'
        'Color original de Snap, sin contraste/gamma/saturacion/HDR/nitidez añadidos por el port.\n'
        'FSR 3.1, FSR 4 compatible y DLSS: preset Nativo/Native AA (DLAA), Calidad, Equilibrado y Rendimiento.\n'
        'Si el runtime necesita actualizarse, el launcher usa el kit incluido y recompila localmente sin descargar herramientas.\n'
        'Conserva tus datos propios, perfiles y partidas. El kit no incluye el juego.\n'
        'Para otro PC: lleva toda la carpeta del launcher y tu GameData; controles en modo Automatico.\n\n'
        'Windows x64, CPU x86-64-v3 (AVX2/FMA/BMI) y GPU/controlador Vulkan 1.3 compatible.\n'
        'Modo TV por defecto; modo portatil disponible. Resolucion interna de 50 a 300%, 30 a 144 FPS y modo VRR.\n'
        'Preparar shaders antes de jugar reconstruye la cache para tu GPU; puede tardar.\n', encoding='utf-8')
    (destination / 'READ-ME-FIRST.txt').write_text(
        f'NewSnapRecomp {VERSION} - MatyMeatBoy\n\n'
        'Extract this entire folder before opening NewSnapLauncher.exe. Keep _internal and the other folders.\n'
        'No Python installation is needed. Your own game data and console keys are not included.\n\n'
        'The launcher follows the Windows display language. Use Language / Idioma to select English or Spanish.\n'
        'Use the single main button at the bottom left: Load game, Verify, Build game if needed, then Play.\n'
        'Load game selects an existing GameData folder without moving it. To import your own dump instead,\n'
        'use Import NSP/XCI/NSZ; the destination is shown before importing.\n'
        'The included public build kit builds the game locally from your verified inputs. Saves and photos are kept.\n'
        'First-time shader preparation may take a while.\n\n'
        'Requires Windows x64, x86-64-v3 CPU (AVX2/FMA/BMI) and a compatible Vulkan 1.3 GPU/driver.\n',
        encoding='utf-8')
    files = {p.relative_to(destination).as_posix(): {'size': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(destination.rglob('*')) if p.is_file()}
    (destination / 'MANIFEST.json').write_text(json.dumps({'version': VERSION,
        'source_revision': revision, 'runtime_api': RUNTIME_API,
        'runtime_capabilities': list(RUNTIME_CAPABILITIES),
        'contains_game_data': False, 'files': files}, indent=2) + '\n', encoding='utf-8')
    if sum(path.stat().st_size for path in destination.rglob('*') if path.is_file()) > MAX_PACKAGE_EXPANDED_BYTES:
        raise ValueError('Expanded Windows package exceeds 2 GiB')
    archive = destination.parent / (name + '.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for file in sorted(destination.rglob('*')):
            if file.is_file():
                output.write(file, Path(name) / file.relative_to(destination))
    if archive.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError('Windows package exceeds 1 GiB')
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    print(json.dumps({'archive': str(archive), 'sha256': checksum, 'source_revision': revision}, indent=2), flush=True)
    return archive


if __name__ == '__main__':
    package()
