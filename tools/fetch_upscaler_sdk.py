"""Fetch only the pinned official AMD FSR Vulkan SDK files; never game inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

COMMIT = '7539ae8b6568ad29ed78a753404351daf3b5cca7'
VERSION = '2.4.0'
DEFAULT_OUT = Path(__file__).resolve().parents[1] / f'toolchain/fsr-sdk-{VERSION}'
BASE = f'https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/{COMMIT}/'
PREFIX = 'Kits/FidelityFX/'
FILES = {
    PREFIX + 'api/include/ffx_api.h': (10848, '4d9dcf243ef5efbf03340a02f16b51a22053243a22e8a9a0b3ce91c26982b4bf'),
    PREFIX + 'api/include/ffx_api_types.h': (13637, '53f07c113a9ba493f297656e4481b6539aed0afc9f3cc8da682aa477d270c46c'),
    PREFIX + 'api/include/vk/ffx_api_vk.h': (12253, '09ac1855bc4c2f711243d6982909385072ca3f8d30db44d1a82ee5bd637832ad'),
    PREFIX + 'upscalers/include/ffx_upscale.h': (19576, '13091e7fe5fd9c82b1fb7c044b9f08f664d9653f599d2ea500738709236fca4d'),
    PREFIX + 'docs/license.md': (65770, '32357259b965d6a8001e9e508ba60eda6034027c5923a7d226ffbaff813c2bfb'),
    '3rdpartynotice.md': (2519, '3b69b1a1011622557a81b55a9a211dd797d01b8160924a5ec51b4c3432d33a4f'),
    PREFIX + 'signedbin/amd_fidelityfx_loader_vk.dll': (39184, '38a56a01fb3565c0757d9f5c1e4e69de4b65e5f2e5769b323b200dc1f142bab9'),
    PREFIX + 'signedbin/amd_fidelityfx_upscaler_vk.dll': (36135696, '4a7e895af6e0b615d40a84d59eb8c2b1054ad91cdd0c739567940270d51bdab7'),
}


def verify_file(path, size, sha256):
    path = Path(path)
    return path.is_file() and path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == sha256


def verify(root):
    return all(verify_file(Path(root) / name, *identity) for name, identity in FILES.items())


def fetch(root, opener=urllib.request.urlopen):
    root = Path(root).resolve()
    for name, (size, digest) in FILES.items():
        target = root / name
        if verify_file(target, size, digest):
            continue
        with opener(BASE + name, timeout=90) as response:
            data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'FSR SDK integrity failure: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.download')
        temporary.write_bytes(data)
        temporary.replace(target)
    (root / 'sdk-receipt.json').write_text(json.dumps({'version': VERSION, 'commit': COMMIT, 'files': FILES}, indent=2) + '\n', encoding='utf-8')
    return root


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'toolchain/fsr-sdk-2.4.0')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        if not verify(args.out):
            parser.exit(1, 'Pinned FSR SDK is missing or changed\n')
    else:
        fetch(args.out)
    print(f'FSR SDK {VERSION}: verified {len(FILES)} pinned files')
