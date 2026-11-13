"""Reproduce the private experimental build using the selected upstream tools."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .adapt import adapt_sources, write_changed
from .importer import write_json
from .upstream import ROOT
from .provenance import verify_import, generation_recipe, record_generation, verify_generation


def run_logged(command, logfile, env=None):
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(x) for x in command], cwd=ROOT, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace')
        for line in process.stdout:
            log.write(line)
            if line.startswith(('main:', 'sdk:', 'total ', 'emitted ', 'emitting ', 'compile:', 'link:', 'objects verified:', 'romfs index:')):
                print(line.rstrip(), flush=True)
        code = process.wait()
    if code:
        print('\n'.join(logfile.read_text(encoding='utf-8').splitlines()[-25:]))
        raise ValueError(f'Build command failed ({code}); see {logfile}')


def build(sdk_root, shader_tools=None, jobs=0, generate=True, cpu='v3'):
    sdk_root = Path(sdk_root).resolve()
    extracted = ROOT / 'build/extracted/updated'
    manifest_path = extracted / 'extraction-manifest.json'
    if not manifest_path.is_file() or not (extracted / 'romfs/import-receipt.json').is_file():
        raise ValueError('Run the verified import before building')
    source = adapt_sources(ROOT / 'build/source', patch_output=ROOT / 'patches/001-snap-bringup.patch')
    print('Checking imported modules, RomFS and control metadata', flush=True)
    manifest, control = verify_import(extracted)
    expected = ROOT / 'build/expected-snap.json'
    write_json(expected, {'exefs_sha256': {f['name']: f['sha256'] for f in manifest['files']}})
    profile = json.loads((ROOT / 'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))
    main_hash = next(f['sha256'] for f in manifest['files'] if f['name'] == 'main')
    patches = ROOT / 'build/snap-runtime-patches.txt'
    write_changed(patches, '\n'.join((ROOT / 'patches' / name).read_text(encoding='utf-8')
                                    for name in ('snap-2.0.1-render.txt', 'snap-2.0.1-supersample.txt')))
    if main_hash != profile['main_sha256']:
        raise ValueError('This runtime adaptation requires the verified Snap 2.0.1 code module')
    gen = ROOT / 'generated/updated'
    recipe = generation_recipe(source, manifest, patches)
    if generate:
        command = [sys.executable, source / 'recomp/gen.py', '--exefs', extracted / 'exefs',
                   '--out', gen, '--version', 'snap', '--patches', patches]
        if jobs:
            command += ['--jobs', str(jobs)]
        run_logged(command, ROOT / 'build/logs/generate.log')
        record_generation(gen, recipe)
    else:
        verify_generation(gen, recipe)
    out = ROOT / 'build/updated'
    decoder = profile['oodle_decompress_offset'] if main_hash == profile['main_sha256'] else 0
    write_changed(out / 'snap_metadata.h', '#pragma once\n'
                  f'#define SNAP_SAVE_SIZE {control["save_size"]}ull\n'
                  f'#define SNAP_JOURNAL_SIZE {control["journal_size"]}ull\n'
                  f'#define SNAP_OODLE_OFFSET {decoder}ull\n')
    command = [sys.executable, source / 'tools/build_game.py', '--version', 'snap', '--gen', gen,
               '--out', out, '--exefs', extracted / 'exefs', '--romfs', extracted / 'romfs',
               '--profile', ROOT / 'build/profile', '--expected', expected, '--toolchain', sdk_root / 'llvm',
               '--deps', sdk_root / 'runtime/deps', '--ninja', sdk_root / 'bin/ninja.exe', '--cpu', cpu]
    if jobs:
        command += ['--jobs', str(jobs)]
    env = dict(os.environ)
    if shader_tools:
        env['NEWSNAP_SHADER_TOOLS'] = str(Path(shader_tools).resolve())
    run_logged(command, ROOT / 'build/logs/compile.log', env)
    for name in ('SDL3.dll', 'libopus-0.dll', 'ac_xlate.exe', 'ac_xlate.id'):
        shutil.copy2(sdk_root / 'bin' / name, out / name)
    print(f'Experimental executable: {out / "newsnap.exe"}', flush=True)
    return out / 'newsnap.exe'
