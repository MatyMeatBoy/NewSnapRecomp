"""Provision the optional pinned official NVIDIA DLSS runtime: Super Resolution and Frame Generation (no game inputs)."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

VERSION = '310.9.16'
COMMIT = '9981c6350dc58c0ce21f024fd65e31e851c31689'
BASE = f'https://raw.githubusercontent.com/NVIDIA/DLSS/{COMMIT}/'
DLL = 'lib/Windows_x86_64/rel/nvngx_dlss.dll'
FG_DLL = 'lib/Windows_x86_64/rel/nvngx_dlssg.dll'   # FG-DLSS: frame generation (RTX 40 and 50 series)
FILES = {
    DLL: (58956912, 'd00b5b0ab29c3ca101b70c3a5ecb3a01b7ef33766a3383a28a18623083e6123e'),
    FG_DLL: (7506544, '8d59d49b36410dd6b62fef2503a5871d347415bd85d943fa0848563a95dd50c7'),
    'LICENSE.txt': (26620, 'd4216e39ebef5f9b50a6712ebb37beeb5379862a67733a9999c651f21592aaf0'),
}
DEFAULT_OUT = Path(__file__).resolve().parents[1] / f'toolchain/dlss-sdk-{VERSION}'
INSTALLED_FILES = {DLL: 'nvngx_dlss.dll', FG_DLL: 'nvngx_dlssg.dll', 'LICENSE.txt': 'licenses/NVIDIA-DLSS.txt'}


def verify_file(path, size, digest):
    path = Path(path)
    return (path.is_file() and path.stat().st_size == size
            and hashlib.sha256(path.read_bytes()).hexdigest() == digest)


def verify(root):
    """Check both the vendor DLL and its accompanying unmodified terms."""
    return all(verify_file(Path(root) / name, *identity) for name, identity in FILES.items())


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.download')
    temporary.write_bytes(data)
    temporary.replace(path)


def _receipt():
    return (json.dumps({'version': VERSION, 'commit': COMMIT, 'source': BASE,
                        'feature': 'Super Resolution / DLAA and Frame Generation', 'files': FILES}, indent=2)
            + '\n').encode('utf-8')


def fetch(root=DEFAULT_OUT, opener=urllib.request.urlopen):
    """Fetch immutable vendor files; reject wrong size/hash before replacing a file."""
    root = Path(root).resolve()
    for name, (size, digest) in FILES.items():
        target = root / name
        if verify_file(target, size, digest):
            continue
        with opener(BASE + name, timeout=90) as response:
            data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'DLSS integrity failure: {name}')
        _write(target, data)
    _write(root / 'sdk-receipt.json', _receipt())
    return root


def install(root, runtime):
    """Place the checked SR DLL beside the executable and retain NVIDIA's terms.

    This is explicit opt-in provisioning. It never supplies the driver's NGX core,
    frame-generation DLL, ray-reconstruction DLL, or modifies a system directory.
    """
    root, runtime = Path(root).resolve(), Path(runtime).resolve()
    # Validate every dependency before touching the destination.
    if not verify(root):
        raise ValueError('Pinned DLSS runtime or license is missing or changed')
    payloads = {name: (root / name).read_bytes() for name in FILES}
    for name, data in payloads.items():
        if hashlib.sha256(data).hexdigest() != FILES[name][1]:
            raise ValueError(f'DLSS source changed during install: {name}')
    for name, target in INSTALLED_FILES.items():
        _write(runtime / target, payloads[name])
    _write(runtime / 'licenses/NVIDIA-DLSS-receipt.json', _receipt())
    return runtime / 'nvngx_dlss.dll'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--verify', action='store_true', help='check cache without downloading')
    parser.add_argument('--install', type=Path, metavar='RUNTIME_DIR', help='opt in: install beside native executable')
    args = parser.parse_args(argv)
    if args.verify:
        if not verify(args.out):
            parser.exit(1, 'Pinned DLSS runtime or license is missing or changed\n')
    else:
        fetch(args.out)
    if args.install:
        print(f'DLSS SR {VERSION}: installed {install(args.out, args.install)}')
    else:
        print(f'DLSS SR {VERSION}: verified {len(FILES)} pinned files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
