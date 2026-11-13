"""Check exactly the Git index that would be committed; never print file contents."""
import re
import subprocess
import hashlib
from pathlib import PurePosixPath

PRIVATE = {'.nsp', '.nsz', '.xci', '.xcz', '.nca', '.ncz', '.tik', '.cert', '.keys', '.nso', '.npdm',
           '.exe', '.dll', '.o', '.obj', '.spv', '.drp', '.wem', '.bin', '.pkz', '.bnsh', '.bntx'}
SECRET = re.compile(rb'^\s*(?:header_key|master_key_[0-9a-f]+|titlekek_[0-9a-f]+|key_area_key_\w+)\s*=\s*[0-9a-f]{32,}', re.I | re.M)

# Exact, visually reviewed original camera artwork from tools/generate_icons.py.
# This exception cannot admit arbitrary renamed game images or binary payloads.
ORIGINAL_ICONS = {
    'apple-touch-icon.png': 'fbde1c7d137599a574e9de8d8d9be0b27ecca0450a6dbaba26387195dde4876d',
    'favicon.ico': '00da948498500aa7a365313513804c6d8d3dc02d13d9267ab3ffa3a3c6dd5abf',
    'icon-128.png': '3344c750cf94b663aba56c8878c472f04a9650fd4a69ee42334f0e4d6ac5a413',
    'icon-16.png': 'b5e62f52a95e369b2d4e960f5586ce9e72c1b212bc6b13a93d89d88f9d39629f',
    'icon-192.png': '119953d0559399b9b89d31638a215084d47e3be3d4d72e04efbe85c3c1b20218',
    'icon-24.png': '270fde986834ce6472506d639f4cd8ee8f2616b57a6ffc034a160e5c864c119a',
    'icon-256.png': 'be827510590560b75c05ba0d9a64db24b4fbd73603eaa6bd7a1345787b8f4052',
    'icon-32.png': 'a91a7051e0bac2707f5b1e9b8db7c96b79527402b90dbc0afa0d5b383abead64',
    'icon-48.png': '2372efb5efd360ade5935fa6dd7a4fa2c49dac6af0f69804a0aa2a1ef0e66101',
    'icon-512.png': 'a61975dc6599006c987dc3eafba37a19999ebf608fbc27c329bbb2893413d37d',
    'icon-64.png': '109ac80809066b3f90f9cc43b0e30ca302ad4398709acbc4d99ed7e900ba3590',
    'newsnap.ico': '3227fe55b20943bf7023b9e16ccb235ac6c5f5aaf20030f56e62b5e871053b70',
}

# Owner-approved original controller artwork; provenance is recorded beside it.
# Pin its exact indexed path, regular-file mode, size, PNG/IHDR and full digest.
CONTROLLER_SPRITE = 'assets/controllers/ultimate2c-sprite.png'
CONTROLLER_SPRITE_SHA256 = 'a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4'
CONTROLLER_SPRITE_HEADER = bytes.fromhex(
    '89504e470d0a1a0a0000000d49484452000000680000004808060000001ab0b097')


def violations(path, content, mode='100644'):
    p = PurePosixPath(path)
    if path == CONTROLLER_SPRITE:
        if (mode == '100644' and len(content) == 8510 and
                content.startswith(CONTROLLER_SPRITE_HEADER) and
                hashlib.sha256(content).hexdigest() == CONTROLLER_SPRITE_SHA256):
            return []
        return ['original controller sprite changed; review its approved bytes and mode']
    if p.parent == PurePosixPath('assets/icons') and p.name in ORIGINAL_ICONS:
        if hashlib.sha256(content).hexdigest() == ORIGINAL_ICONS[p.name]:
            return []
        return ['original icon changed; review and regenerate its approved hash']
    errors = []
    if mode == '160000':
        return [] if path == 'third_party/astral' else ['unapproved submodule']
    if p.suffix.lower() in PRIVATE or p.name in ('main', 'sdk', 'rtld', 'config.local.toml'):
        errors.append('private input or binary')
    if p.parts[0] in ('build', 'generated', 'game', 'toolchain', '.venv'):
        errors.append('private output directory')
    if len(content) > 2 * 1024 * 1024 or b'\0' in content:
        errors.append('binary or oversized content')
    if SECRET.search(content):
        errors.append('key assignment')
    if content.startswith((b'// GENERATED GAME CODE', b'// AC_RECOMP_' + b'GENERATED_FROM_GAME_CODE')):
        errors.append('generated game code')
    return errors


def main():
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z']).split(b'\0')
    failures = []
    count = 0
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, _, stage = metadata.decode().split()
        path = raw_path.decode('utf-8')
        if stage != '0':
            failures.append((path, ['unmerged index']))
            continue
        content = b'' if mode == '160000' else subprocess.check_output(['git', 'show', ':' + path])
        problems = violations(path, content, mode)
        if problems:
            failures.append((path, problems))
        count += 1
    for path, problems in failures:
        print(f'{path}: {", ".join(problems)}')
    print(f'Content check: {count} index entries, {len(failures)} rejected')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
