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

# Owner-requested, visually reviewed official promotional artwork. Its source
# and copyright are recorded in assets/launcher/{README.md,source-pins.json};
# those mutable documents cannot grant permission to different indexed bytes.
# No project-code or redistribution licence is implied by these narrow pins.
PROMOTIONAL_JPEG_HEADER = bytes.fromhex('ffd8ffe000104a46494600010100000100010000')
PROMOTIONAL_ASSETS = {
    # Owner-requested illustrated README summaries (2026-11-16), generated with
    # ImageGen and visually reviewed; provenance in docs/showcase/README.md.
    # These are not official artwork or raw gameplay captures. Exact bytes only.
    'docs/showcase/overview.png': (
        2186463, bytes.fromhex('89504e470d0a1a0a0000000d4948445200000688000003ad08020000003de4705e'),
        'f8a5435d492cc4bd5c777c49042923402516dccb204b28ccd9dc1f5b44c981e8'),
    'docs/showcase/comparison.png': (
        2212379, bytes.fromhex('89504e470d0a1a0a0000000d4948445200000688000003ad08020000003de4705e'),
        '2a13e418cecedd5ac3fdbfceb90564b73350fbd8b458773f14aa89aa622ab557'),
    'assets/launcher/lental-hero.jpg': (
        21580, PROMOTIONAL_JPEG_HEADER,
        '4758d49e5aa462310c050147d2a9d96bb0b09a377389bec0163767a0a7978f81'),
    'assets/launcher/lental-explore.jpg': (
        4966, PROMOTIONAL_JPEG_HEADER,
        'ef88386ca3469a99c28ac2fa0d71130d55e7066b999d263773a6cc5ab90e87b2'),
    'assets/launcher/snap-logo.png': (
        41783, bytes.fromhex('89504e470d0a1a0a0000000d49484452000001e40000011b08030000003cb40707'),
        '8cb13d97a86a9a2c88d29579597775aa02466ca7acbaf2dad828fe1d7997299b'),
    # Owner-requested README screenshots (2026-11-14): runtime window captures on the
    # owner's RX 6900 XT, no saves, photos or keys; pinned to their exact bytes.
    'docs/images/camp-175.jpg': (
        207798, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        '61b834f8a91ae66ac356a08aa3c88ecdb7ec9bde8d63020bfc7042d419b9630c'),
    'docs/images/display-1440p.jpg': (
        118167, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        'afacac5174a35627defd8706eb7f31fc1a87eb300c45b1daff6a26e1bf9cdb25'),
    'docs/images/evaluation-200.jpg': (
        74045, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        '468edf07793a06a9e0a0e0353512d7dca5be327f1c9b3e6552bcf05eb45df0a4'),
    'docs/images/expedition-200.jpg': (
        169356, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        '46da1cdc81440899c279dd6110b9dbb93c59bc130aea7c13c4dd6489a42e4dd8'),
    'docs/images/aa-fsr4-native.jpg': (   # owner-requested anti-aliasing comparison (2026-11-15), same capture rules
        146770, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        '514c71168b8a52c404c82b9d2b3063d177e54f90977d75b760f68b635c1e7d5b'),
    # Owner-requested README picture of the 0.9.20 launcher (2026-11-15): a capture of the launcher's own window
    # (Mejoras page, artwork drawn by the launcher), no game picture, saves, photos, keys or local paths.
    'docs/images/launcher-0920.jpg': (
        148969, bytes.fromhex('ffd8ffe000104a46494600010100000100010000'),
        '1f31b80cbab8e8380cb6f5312c7cb044ac7f1dce12222f3d5614e81b09debdf4'),
}

# The launcher's typeface: Nunito, SIL Open Font License 1.1 (licenses/Nunito-OFL.txt), the unmodified variable
# font from github.com/google/fonts (ofl/nunito) at commit 8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5; provenance in
# assets/fonts/README.md. Pinned to its exact indexed path, regular-file mode, size, sfnt header and digest.
OPEN_FONTS = {
    'assets/fonts/Nunito[wght].ttf': (
        276932, bytes.fromhex('00010000'),
        'bb55a5ca5c2042335b3991af27c4d0705d0ef41cac6164ac737fd8f2a1e85207'),
}


def violations(path, content, mode='100644'):
    p = PurePosixPath(path)
    if path in OPEN_FONTS:
        size, header, checksum = OPEN_FONTS[path]
        if (mode == '100644' and len(content) == size and content.startswith(header) and
                hashlib.sha256(content).hexdigest() == checksum):
            return []
        return ['open-licence font changed; review its approved path, bytes and mode']
    if path in PROMOTIONAL_ASSETS:
        size, header, checksum = PROMOTIONAL_ASSETS[path]
        if (mode == '100644' and len(content) == size and content.startswith(header) and
                hashlib.sha256(content).hexdigest() == checksum):
            return []
        return ['official promotional artwork changed; review its approved path, bytes and mode']
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
    if p.suffix.lower() in PRIVATE | {'.jpg', '.jpeg', '.png'} or p.name in ('main', 'sdk', 'rtld', 'config.local.toml'):
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
