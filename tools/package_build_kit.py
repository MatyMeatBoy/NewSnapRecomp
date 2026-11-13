"""Package public recipe + portable compiler/Python; never include owner inputs.

Usage: python -m tools.package_build_kit --sdk-root "toolchain/.../Astral Chain-Setup"
The resulting checksum-bound asset belongs to the same release as the launcher.
"""
import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from newsnap.maintenance import digest, verify_build_kit
from newsnap.upstream import ROOT, COMMIT
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES


def archive_path(target):
    return target.parent / (target.name + '.zip')


def verify_kit_tree(folder):
    forbidden = {'.nsp', '.nsz', '.xci', '.xcz', '.nca', '.nso', '.npdm', '.keys', '.drp', '.nushdb', '.bin'}
    for path in folder.rglob('*'):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Build kits cannot contain links')
        relative = path.relative_to(folder)
        if (any(part.lower() in ('gamedata', 'newsnapgamedata') for part in relative.parts) or
                relative.parts[0] == 'source' and any(part.lower() in ('generated', 'extracted', 'profile')
                                                     for part in relative.parts)):
            raise ValueError('Owner/private directories cannot enter a build kit')
        if path.suffix.lower() in forbidden or path.name.lower() in ('main', 'sdk', 'newsnap.exe', 'romfs.bin') and path.is_file():
            raise ValueError('Game-derived or private content in build kit')


def _copy(source, destination):
    if source.is_dir():
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', '.lock'))
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def package(sdk_root, destination=None, shader_tools=None, allow_dirty=False):
    sdk = Path(sdk_root).resolve()
    if not allow_dirty and subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--ignore-submodules=none'], cwd=ROOT).returncode:
        raise ValueError('Commit the recipe before closing a public build kit')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    donor = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT / 'third_party/astral', text=True).strip()
    if donor != COMMIT:
        raise ValueError('The donor checkout differs from the pinned source revision')
    target = Path(destination) if destination else ROOT / 'build/releases' / f'NewSnapBuildKit-{VERSION}-windows-{revision[:8]}'
    target.mkdir(parents=True, exist_ok=False)
    for name in ('newsnap', 'patches', 'profiles', 'assets/icons', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        _copy(ROOT / name, target / 'source' / name)
    for name in ('fetch_upscaler_sdk.py', 'fetch_dlss.py'):
        _copy(ROOT / 'tools' / name, target / 'source/tools' / name)
    # The pinned official SDK cache is public. It avoids network access during an
    # owner rebuild and supplies headers as well as redistributable DLLs/terms.
    for name in ('fsr-sdk-2.4.0', 'dlss-sdk-310.9.16'):
        if (ROOT / 'toolchain' / name).is_dir():
            _copy(ROOT / 'toolchain' / name, target / 'source/toolchain' / name)
    for name in ('runtime', 'recomp', 'tools', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        _copy(ROOT / 'third_party/astral' / name, target / 'source/third_party/astral' / name)
    _copy(sdk / 'python', target / 'python')
    # Embedded Python must import the public recipe without relying on host PATH,
    # a Python installation, registry entries, user site packages, or working dir.
    pth_files = list((target / 'python').glob('python*._pth'))
    if len(pth_files) != 1:
        raise ValueError('Expected a portable embedded Python with one ._pth file')
    pth = pth_files[0]
    lines = [line for line in pth.read_text().splitlines() if line and not line.startswith('#')]
    lines = [line for line in lines if line not in ('..', '../tools', '../recomp', 'import site')]
    pth.write_text('\n'.join(lines + ['../source']) + '\n', encoding='utf-8')
    for name in ('llvm', 'runtime/deps', 'licenses'):
        if (sdk / name).exists():
            _copy(sdk / name, target / 'sdk' / name)
    for name in ('ninja.exe', 'SDL3.dll', 'libopus-0.dll', 'ac_xlate.exe', 'ac_xlate.id', 'libxess.dll'):
        if (sdk / 'bin' / name).exists():
            _copy(sdk / 'bin' / name, target / 'sdk/bin' / name)
    for name in ('THIRD_PARTY_NOTICES.md', 'VERSION'):
        _copy(sdk / name, target / 'sdk' / name)
    # These SPIR-V words are AMD's public native FSR passes, not game shaders.
    # Verify their exact source recipe before adding the portable build asset.
    from newsnap.build import stage_runtime_shaders
    shader_header = ROOT / 'build/updated/fsr3_spv.h'
    pin = json.loads((ROOT / 'profiles/runtime-shaders.json').read_text(encoding='utf-8'))
    if digest(shader_header) != pin['fsr3_spv_sha256']:
        raise ValueError('Rebuild the pinned public native shader header before packaging')
    _copy(shader_header, target / 'sdk/precompiled/fsr3_spv.h')
    stage_runtime_shaders(target / 'sdk', target / 'source/third_party/astral', target / 'shader-check')
    shutil.rmtree(target / 'shader-check')
    license_path = ROOT / 'build/source/toolchain/ffx-sdk/c6efa6bf7f2027b3ec94f28578bb5965eabb9e55/LICENSE.txt'
    _copy(license_path, target / 'sdk/licenses/FidelityFX-SDK-1.1.4-LICENSE.txt')
    if shader_tools:
        # Includes the tool distribution's DLLs and license; do not copy host SDKs.
        _copy(Path(shader_tools), target / 'sdk/shader-tools')
    verify_kit_tree(target)
    files = {p.relative_to(target).as_posix(): digest(p) for p in sorted(target.rglob('*')) if p.is_file()}
    manifest = {'format': 1, 'runtime_version': VERSION, 'runtime_api': RUNTIME_API,
                'capabilities': list(RUNTIME_CAPABILITIES), 'source_revision': revision,
                'donor_commit': COMMIT, 'sdk_version': (sdk / 'VERSION').read_text().strip(),
                'contains_game_data': False, 'files': files}
    (target / 'build-kit.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    verify_build_kit(target)
    archive = archive_path(target)
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in sorted(target.rglob('*')):
            if path.is_file():
                output.write(path, Path(target.name) / path.relative_to(target))
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    print(json.dumps({'archive': str(archive), 'sha256': checksum, 'source_revision': revision}), flush=True)
    return target, archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--shader-tools', type=Path)
    args = parser.parse_args()
    package(args.sdk_root, args.destination, args.shader_tools)
