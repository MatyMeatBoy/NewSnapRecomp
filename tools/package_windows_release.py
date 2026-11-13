"""Close a standalone launcher release. Owner GameData is always excluded."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile

from tools.build_launcher import ROOT, source_fingerprints
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES


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
    name = f'NewSnapRecomp-{VERSION}-windows-{revision[:8]}'
    destination = ROOT / 'build/releases' / name
    shutil.copytree(candidate, destination)
    (destination / 'LEEME.txt').write_text(
        f'NewSnapRecomp {VERSION} - MatyMeatBoy\n\n'
        'Extrae toda esta carpeta. Copia tu carpeta GameData junto a NewSnapLauncher.exe.\n'
        'Abre NewSnapLauncher.exe. Conserva _internal y las otras carpetas de la release.\n'
        'No requiere instalar Python. GameData no se incluye en GitHub.\n\n'
        '0.4: color original de Snap, sin contraste/gamma/saturacion/HDR/nitidez añadidos por el port.\n'
        'FSR 3.1, FSR 4 compatible y DLSS: preset Nativo/Native AA (DLAA), Calidad, Equilibrado y Rendimiento.\n'
        'Si el runtime necesita actualizarse, el launcher obtiene el kit de esta misma version y recompila localmente.\n'
        'Conserva tus datos propios, perfiles y partidas. El kit no incluye el juego.\n'
        'Para otro PC: lleva toda la carpeta del launcher y tu GameData; controles en modo Automatico.\n\n'
        'Windows x64, CPU x86-64-v3 (AVX2/FMA/BMI) y GPU/controlador Vulkan 1.3 compatible.\n'
        'Probado fisicamente en RTX 4060; AMD sigue pendiente de hardware real.\n'
        'Modo TV por defecto; modo portatil disponible. Escalas 125/150/200% experimentales solo TV.\n'
        'Mas de 60 FPS, recorridos completos y fotografia en todas las escalas siguen sin verificar.\n'
        'Preparar shaders antes de jugar reconstruye la cache para tu GPU; puede tardar.\n', encoding='utf-8')
    files = {p.relative_to(destination).as_posix(): {'size': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(destination.rglob('*')) if p.is_file()}
    (destination / 'MANIFEST.json').write_text(json.dumps({'version': VERSION,
        'source_revision': revision, 'runtime_api': RUNTIME_API,
        'runtime_capabilities': list(RUNTIME_CAPABILITIES),
        'contains_game_data': False, 'files': files}, indent=2) + '\n', encoding='utf-8')
    archive = destination.parent / (name + '.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for file in sorted(destination.rglob('*')):
            if file.is_file():
                output.write(file, Path(name) / file.relative_to(destination))
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    print(json.dumps({'archive': str(archive), 'sha256': checksum, 'source_revision': revision}, indent=2), flush=True)
    return archive


if __name__ == '__main__':
    package()
