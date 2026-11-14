"""Build toolchain/hactool/hactool.exe for the launcher's NSP/XCI import, without MSYS2.

SciresM/hactool at the donor's pinned commit plus the donor's three patches
(third_party/astral/tools/hactool/*.patch), compiled with the SDK root's clang
(x86_64-w64-windows-gnu). mbedtls's network module is left out: hactool never uses it.

  python tools/build_hactool.py --sdk-root D:\\01Claude\\NewSnapRecomp\\sdkroot
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/SciresM/hactool.git'
COMMIT = '1d64a83450e025622f3468c28fc4164dad2c5ef6'
PATCHES = ('portable', 'unicode', 'mbedtls-asm-clobbers')


def build(sdk_root, out=ROOT / 'toolchain/hactool'):
    llvm = Path(sdk_root) / 'llvm/bin'
    with tempfile.TemporaryDirectory(prefix='hactool-') as temporary:
        src = Path(temporary) / 'src'
        subprocess.run(['git', 'clone', '-q', URL, str(src)], check=True)
        subprocess.run(['git', '-C', str(src), 'checkout', '-q', COMMIT], check=True)
        for name in PATCHES:
            subprocess.run(['git', '-C', str(src), 'apply', '--whitespace=nowarn',
                            str(ROOT / f'third_party/astral/tools/hactool/{name}.patch')], check=True)
        objects = []
        sources = [p for p in (src / 'mbedtls/library').glob('*.c') if p.name != 'net_sockets.c'] + list(src.glob('*.c'))
        for c in sources:
            o = c.with_suffix('.o')
            subprocess.run([str(llvm / 'clang.exe'), '-O2', '-std=gnu11', '-D_FILE_OFFSET_BITS=64',
                            '-I', str(src / 'mbedtls/include'), '-c', str(c), '-o', str(o)], check=True, cwd=src)
            objects.append(str(o))
        subprocess.run([str(llvm / 'llvm-windres.exe'), 'hactool.rc', '-O', 'coff', '-o', 'res.o'], check=True, cwd=src)
        subprocess.run([str(llvm / 'clang.exe'), *objects, str(src / 'res.o'), '-static', '-o', 'hactool.exe',
                        '-ladvapi32', '-lws2_32'], check=True, cwd=src)
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / 'hactool.exe', out / 'hactool.exe')
        shutil.copy2(src / 'LICENSE', out / 'LICENSE')
    return out / 'hactool.exe'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    print(build(parser.parse_args().sdk_root))
