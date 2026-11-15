"""Reproduce the private experimental build using the selected upstream tools."""
import json
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .adapt import adapt_sources, write_changed
from .importer import write_json
from .upstream import ROOT
from .provenance import verify_import, generation_recipe, record_generation, verify_generation
from .importer import source_digest
from .random_range_adapt import verify_original as verify_random_range_original
from .translator import verify_translator, stage_translator


def python_script_command(script, *arguments):
    """Embedded Python's ._pth omits script directories; provide the owned one."""
    bootstrap = ('import sys,runpy; from pathlib import Path; '
                 'script=sys.argv[1]; sys.path.insert(0,str(Path(script).resolve().parent)); '
                 'sys.argv=sys.argv[1:]; runpy.run_path(script,run_name="__main__")')
    return [sys.executable, '-c', bootstrap, str(script), *arguments]


def stage_runtime_shaders(sdk_root, source, out):
    """Use an exact public native-shader header when the portable kit supplies it."""
    header = Path(sdk_root) / 'precompiled/fsr3_spv.h'
    if not header.is_file():
        return False
    pin = json.loads((ROOT / 'profiles/runtime-shaders.json').read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('newsnap_public_shader_recipe', source / 'tools/ffx_sdk.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stamp = '// recipe sha256 ' + module.recipe_hash()
    if (source_digest(header) != pin['fsr3_spv_sha256'] or
            module.recipe_hash() != pin['fsr3_recipe_sha256'] or
            stamp not in header.read_text(encoding='utf-8').splitlines()[:3]):
        raise ValueError('Public native shader header differs from the pinned donor recipe')
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(header, out / 'fsr3_spv.h')
    terms = Path(sdk_root) / 'licenses/FidelityFX-SDK-1.1.4-LICENSE.txt'
    if terms.is_file():
        (out / 'licenses').mkdir(exist_ok=True)
        shutil.copy2(terms, out / 'licenses' / terms.name)
    return True


def run_logged(command, logfile, env=None):
    from .progress import parse_progress_line, unbuffered_command, MAX_LINE_BYTES
    environment=dict(os.environ if env is None else env)
    environment['PYTHONUNBUFFERED']='1'
    environment['NINJA_STATUS']='[%f/%t] '
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(unbuffered_command(command), cwd=ROOT, env=environment,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace')
        try:
            # Real pipes expose readline(size): cap each allocation even when a
            # compiler emits a huge line. Iterable-only test/error wrappers
            # retain their existing cleanup contract.
            bounded=callable(getattr(process.stdout,'readline',None))
            lines=iter(lambda:process.stdout.readline(MAX_LINE_BYTES+1),'') if bounded else iter(process.stdout)
            discarding=False
            for line in lines:
                log.write(line)
                log.flush()
                oversized=len(line.encode('utf-8',errors='replace'))>MAX_LINE_BYTES
                skip=discarding or oversized
                discarding=(discarding or oversized) and not line.endswith('\n')
                if skip:continue
                update=parse_progress_line(line)
                if update is not None and update.current is not None:
                    print(f'[{update.current}/{update.total}] Compilación local' if update.stage=='compile'
                          else f'emitted {update.current}/{update.total} chunks',flush=True)
                elif len(line.encode('utf-8',errors='replace'))<=MAX_LINE_BYTES and line.startswith(('main:', 'sdk:', 'total ', 'emitted ', 'emitting ', 'compile:', 'link:', 'objects verified:', 'romfs index:')):
                    print(line.rstrip(), flush=True)
            code = process.wait()
        except BaseException:
            # Callers may restore previous outputs immediately after we raise.
            # The owned producer must have stopped writing before that rollback.
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        finally:
            process.stdout.close()
    if code:
        with logfile.open('rb') as stream:
            stream.seek(max(0,logfile.stat().st_size-(64<<10)))
            print('\n'.join(stream.read(64<<10).decode('utf-8',errors='replace').splitlines()[-25:]),flush=True)
        raise ValueError(f'Build command failed ({code}); see {logfile}')


def build(sdk_root, shader_tools=None, jobs=0, generate=True, cpu='v3', *, owner_data=None, work_dir=None,
          generation_cache_root=None):
    sdk_root = Path(sdk_root).resolve()
    verify_translator(sdk_root / 'bin')
    work = Path(work_dir).resolve() if work_dir else ROOT / 'build'
    profile = json.loads((ROOT / 'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))
    if owner_data is None:
        extracted = ROOT / 'build/extracted/updated'
        manifest_path = extracted / 'extraction-manifest.json'
        if not manifest_path.is_file() or not (extracted / 'romfs/import-receipt.json').is_file():
            raise ValueError('Run the verified import before building')
        print('Checking imported modules, RomFS and control metadata', flush=True)
        manifest, control = verify_import(extracted)
        exefs, romfs = extracted / 'exefs', extracted / 'romfs'
    else:
        from .maintenance import verify_owner_inputs
        from .upstream import extractor
        owner_data = Path(owner_data).resolve()
        print('Checking original owner modules and RomFS against the supported-version recipe', flush=True)
        manifest, control = verify_owner_inputs(owner_data, profile)
        exefs = owner_data / 'exefs'
        romfs = work / 'owner-romfs'
        romfs.mkdir(parents=True, exist_ok=True)
        image = owner_data / 'romfs/romfs.bin'
        staged = romfs / 'romfs.bin'
        if not staged.exists():
            # Same volume for normal maintenance; no duplicate 7 GiB image.
            try:
                os.link(image, staged)
            except OSError:
                shutil.copyfile(image, staged)
        write_json(romfs / 'index.json', {'status': 'pass', 'romfs_size': image.stat().st_size,
                   'romfs_sha256': profile['romfs_sha256'], 'files': extractor().index_romfs(image)})
    source = adapt_sources(work / 'source', patch_output=(work / 'snap-bringup.patch' if owner_data else
                                                        ROOT / 'patches/001-snap-bringup.patch'))
    if not stage_runtime_shaders(sdk_root, source, work / 'updated') and owner_data:
        raise ValueError('Owner rebuild requires the public native shader header from its build kit')
    expected = work / 'expected-snap.json'
    write_json(expected, {'exefs_sha256': {f['name']: f['sha256'] for f in manifest['files']}})
    main_hash = next(f['sha256'] for f in manifest['files'] if f['name'] == 'main')
    patches = work / 'snap-runtime-patches.txt'
    write_changed(patches, '\n'.join((ROOT / 'patches' / name).read_text(encoding='utf-8')
                                    for name in ('snap-2.0.1-render.txt', 'snap-2.0.1-supersample.txt',
                                                 'snap-2.0.1-random-range.txt',
                                                 'snap-2.0.1-high-fps.txt', 'snap-2.0.1-wide.txt')))
    if main_hash != profile['main_sha256']:
        raise ValueError('This runtime adaptation requires the verified Snap 2.0.1 code module')
    verify_random_range_original(exefs)
    gen = work / 'generated' if owner_data else ROOT / 'generated/updated'
    recipe = generation_recipe(source, manifest, patches)
    cache, identity, restored = None, None, False
    lookup_seconds = generation_seconds = publish_seconds = 0.0
    if owner_data and generate:
        from .generation_cache import GenerationCache, owner_identity
        # Original ExeFS and the entire RomFS were verified above, even on a hit.
        identity = owner_identity(owner_data, manifest, profile['romfs_sha256'])
        cache = GenerationCache(generation_cache_root)
        started = time.perf_counter()
        restored = cache.restore(identity, recipe, gen)
        lookup_seconds = time.perf_counter() - started
        if restored:
            print('generation cache: reused independently copied, verified private code', flush=True)
    if generate:
        if not restored:
            command = [sys.executable, source / 'recomp/gen.py', '--exefs', exefs,
                       '--out', gen, '--version', 'snap', '--patches', patches]
            if jobs:
                command += ['--jobs', str(jobs)]
            started = time.perf_counter()
            run_logged(command, work / 'logs/generate.log')
            record_generation(gen, recipe)
            generation_seconds = time.perf_counter() - started
            if cache:
                started = time.perf_counter()
                cache.publish(identity, recipe, gen)
                publish_seconds = time.perf_counter() - started
    else:
        verify_generation(gen, recipe)
    if owner_data:
        write_json(work / 'logs/generation-cache.json', {
            'format': 1, 'restored': restored, 'generator_ran': bool(generate and not restored),
            'cache_status': cache.status if cache else 'unused', 'lookup_seconds': lookup_seconds,
            'generation_seconds': generation_seconds, 'publish_seconds': publish_seconds,
            'generator_environment': cache.generator_environment if cache else None})
    out = work / 'updated'
    decoder = profile['oodle_decompress_offset'] if main_hash == profile['main_sha256'] else 0
    write_changed(out / 'snap_metadata.h', '#pragma once\n'
                  f'#define SNAP_SAVE_SIZE {control["save_size"]}ull\n'
                  f'#define SNAP_JOURNAL_SIZE {control["journal_size"]}ull\n'
                  f'#define SNAP_OODLE_OFFSET {decoder}ull\n')
    command = python_script_command(source / 'tools/build_game.py', '--version', 'snap', '--gen', gen,
               '--out', out, '--exefs', exefs, '--romfs', romfs,
               '--profile', work / 'probe-profile' if owner_data else ROOT / 'build/profile',
               '--expected', expected, '--toolchain', sdk_root / 'llvm',
               '--deps', sdk_root / 'runtime/deps', '--ninja', sdk_root / 'bin/ninja.exe', '--cpu', cpu)
    if jobs:
        command += ['--jobs', str(jobs)]
    env = dict(os.environ)
    from tools.fetch_upscaler_sdk import DEFAULT_OUT as FSR_DEFAULT, verify as verify_fsr
    from .upscaler_adapt import stage_sdk
    fsr_sdk = Path(env.get('NEWSNAP_FSR_SDK', str(FSR_DEFAULT))).resolve()
    if not verify_fsr(fsr_sdk):
        raise ValueError('Missing verified FSR SDK: run python tools/fetch_upscaler_sdk.py before building')
    env['NEWSNAP_FSR_SDK'] = str(fsr_sdk)
    if shader_tools:
        env['NEWSNAP_SHADER_TOOLS'] = str(Path(shader_tools).resolve())
    run_logged(command, work / 'logs/compile.log', env)
    for name in ('SDL3.dll', 'libopus-0.dll'):
        shutil.copy2(sdk_root / 'bin' / name, out / name)
    stage_translator(sdk_root / 'bin', out)
    stage_sdk(fsr_sdk, out)
    from tools.fetch_dlss import DEFAULT_OUT as DLSS_DEFAULT, verify as verify_dlss, install as install_dlss
    if verify_dlss(DLSS_DEFAULT):
        install_dlss(DLSS_DEFAULT, out)
    print(f'Experimental executable: {out / "newsnap.exe"}', flush=True)
    return out / 'newsnap.exe'
