"""Check exactly the Git index that would be committed; never print file contents."""
import re
import subprocess
from pathlib import PurePosixPath

PRIVATE = {'.nsp', '.nsz', '.xci', '.xcz', '.nca', '.ncz', '.tik', '.cert', '.keys', '.nso', '.npdm',
           '.exe', '.dll', '.o', '.obj', '.spv', '.drp', '.wem', '.bin', '.pkz', '.bnsh', '.bntx'}
SECRET = re.compile(rb'^\s*(?:header_key|master_key_[0-9a-f]+|titlekek_[0-9a-f]+|key_area_key_\w+)\s*=\s*[0-9a-f]{32,}', re.I | re.M)


def violations(path, content, mode='100644'):
    p = PurePosixPath(path)
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
