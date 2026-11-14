"""Execute actual prepared C# emitter methods against independent public oracles."""
import importlib.util
import os
from pathlib import Path
import shutil
import json
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / 'third_party/astral'


def method(source, name):
    start = source.index('        private static void ' + name + '(')
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def prepared(directory, adapted):
    stage = directory / 'stage'
    patches = stage / 'tools/xlate/patches'
    shutil.copytree(DONOR / 'tools/xlate/patches', patches)
    source = (DONOR / 'tools/build_xlate.py').read_text(encoding='utf-8')
    if adapted:
        from newsnap.xlate_semantics_adapt import edits, stage_patches
        for old, new in edits()['tools/build_xlate.py']:
            if source.count(old) != 1:
                raise AssertionError('donor build script anchor changed')
            source = source.replace(old, new, 1)
        stage_patches(stage)
    script = stage / 'tools/build_xlate.py'
    script.write_text(source, encoding='utf-8')
    spec = importlib.util.spec_from_file_location('fixture_xlate_build', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BUILD = directory / 'prepared'
    module.BUILD.mkdir()
    module.VENDOR = DONOR / 'tools/vendor/ryujinx'
    return module, module.prepare_sources() / 'src/Ryujinx.Graphics.Shader'


def compile_fixture(directory, dotnet, adapted=True):
    _, source = prepared(directory, adapted)
    bitfield = (source / 'Instructions/InstEmitBitfield.cs').read_text(encoding='utf-8')
    shift = (source / 'Instructions/InstEmitShift.cs').read_text(encoding='utf-8')
    methods = [method(bitfield, 'EmitBfe'), method(bitfield, 'EmitBfi'), method(shift, 'EmitShf')]
    if 'private static void ClampBitfield(' in bitfield:
        methods.append(method(bitfield, 'ClampBitfield'))
    project = directory / 'fixture'
    project.mkdir()
    fixture = (ROOT / 'tests/fixtures/xlate_semantics.cs').read_text(encoding='utf-8')
    (project / 'Program.cs').write_text(fixture.replace('@METHODS@', '\n'.join(methods)), encoding='utf-8')
    (project / 'fixture.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>', encoding='utf-8')
    (project / 'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>', encoding='utf-8')
    env = os.environ.copy()
    env.update(DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_NOLOGO='1', DOTNET_CLI_HOME=str(directory / 'dotnet-home'))
    result = subprocess.run([dotnet, 'build', str(project / 'fixture.csproj'), '-c', 'Release', '-o', str(project / 'out'), '--nologo'], capture_output=True, text=True, env=env, timeout=120)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return project / 'out/fixture.dll', env


class XlateSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dotnet = os.environ.get('NEWSNAP_DOTNET') or shutil.which('dotnet')
        if not cls.dotnet or not (DONOR / 'tools/vendor/ryujinx').is_dir():
            raise unittest.SkipTest('.NET 10 SDK and initialized public donor required')
        probe = subprocess.run([cls.dotnet, '--list-sdks'], text=True, capture_output=True, timeout=20)
        has_sdk = probe.returncode == 0 and any(line.startswith('10.') for line in probe.stdout.splitlines())
        if not has_sdk:
            if os.environ.get('NEWSNAP_DOTNET'):
                raise AssertionError('NEWSNAP_DOTNET must provide a .NET 10 SDK: ' + probe.stdout + probe.stderr)
            raise unittest.SkipTest('.NET host found, but .NET 10 SDK is not installed')
        base = Path(os.environ.get('NEWSNAP_XLATE_PROOF_DIR', ROOT / 'build/xlate-semantics-proof'))
        base.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='emitter-', dir=base)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.program, cls.env = compile_fixture(Path(cls.temp.name), cls.dotnet)

    def run_fixture(self, mode):
        result = subprocess.run([self.dotnet, str(self.program), mode], env=self.env, text=True, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_actual_bfe_bfi_constant_dynamic_signed_and_reversed(self):
        self.assertIn('cases=655360 failures=0', self.run_fixture('bitfield'))

    def test_actual_funnel_modes_endpoints_cc_and_all_intermediates_defined(self):
        self.assertIn('failures=0', self.run_fixture('funnel'))


class XlatePatchStagingTests(unittest.TestCase):
    def test_preserves_original_motion_and_all_twelve_patches(self):
        from newsnap.xlate_semantics_adapt import stage_patches, EXPECTED_PATCHES, ORIGINAL_PATCHES
        with tempfile.TemporaryDirectory() as name:
            stage = Path(name)
            target = stage / 'tools/xlate/patches'
            shutil.copytree(DONOR / 'tools/xlate/patches', target)
            originals = {p: (target / p).read_bytes() for p in ORIGINAL_PATCHES}
            stage_patches(stage)
            stage_patches(stage)
            self.assertEqual(tuple(sorted(p.name for p in target.glob('*.patch'))), EXPECTED_PATCHES)
            self.assertEqual({p: (target / p).read_bytes() for p in ORIGINAL_PATCHES}, originals)

    def test_unknown_or_missing_patch_is_rejected_without_deleting_it(self):
        from newsnap.xlate_semantics_adapt import stage_patches
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / 'tools/xlate/patches'
            shutil.copytree(DONOR / 'tools/xlate/patches', target)
            extra = target / '0999-unreviewed.patch'
            extra.write_text('unreviewed')
            with self.assertRaises(ValueError):
                stage_patches(name)
            self.assertEqual(extra.read_text(), 'unreviewed')
            extra.unlink()
            (target / '0012-motion-previous-position.patch').unlink()
            with self.assertRaises(ValueError):
                stage_patches(name)

    def test_actual_builder_rejects_fourteen_wrong_names(self):
        base = Path(os.environ.get('NEWSNAP_XLATE_PROOF_DIR', ROOT / 'build/xlate-semantics-proof'))
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='guard-', dir=base) as name:
            module, _ = prepared(Path(name), True)
            patch = module.XLATE / 'patches/0012-motion-previous-position.patch'
            patch.rename(patch.with_name('0012-wrong.patch'))
            with self.assertRaisesRegex(SystemExit, 'exact 14'):
                module.prepare_sources()


class FullTranslatorSyntheticTests(unittest.TestCase):
    def test_public_maxwell_programs_translate_and_validate(self):
        dotnet = os.environ.get('NEWSNAP_DOTNET') or shutil.which('dotnet')
        dll = os.environ.get('NEWSNAP_XLATE_DLL')
        executable = os.environ.get('NEWSNAP_XLATE_EXE')
        validator = os.environ.get('NEWSNAP_SPIRV_VALIDATOR')
        if not validator or not (executable or (dotnet and dll)):
            self.skipTest('set NEWSNAP_XLATE_EXE (or DOTNET/DLL) and NEWSNAP_SPIRV_VALIDATOR for full tool proof')
        fixture = ROOT / 'tests/fixtures/xlate_programs.py'
        spec = importlib.util.spec_from_file_location('public_maxwell_programs', fixture)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        base = Path(os.environ.get('NEWSNAP_XLATE_PROOF_DIR', ROOT / 'build/xlate-semantics-proof'))
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='synthetic-', dir=base) as name:
            directory = Path(name)
            jobs = []
            for key, code in module.programs(DONOR).items():
                path = directory / (key + '.bin')
                path.write_bytes(code)
                for debug in (False, True):
                    jobs.append(dict(key=key + ('-debug' if debug else '-optimized'), stage='cs',
                                     code=str(path), local=[8, 8, 1], shared=256, debug=debug))
            requests = directory / 'jobs.json'
            requests.write_text(json.dumps(jobs), encoding='utf-8')
            output = directory / 'out'
            env = os.environ.copy()
            env['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
            result = subprocess.run(([executable] if executable else [dotnet, dll]) + [str(requests), str(output)], env=env,
                                    capture_output=True, text=True, encoding='utf-8', timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(list(output.glob('*.spv'))), 18)
            for job in jobs:
                with self.subTest(shader=job['key']):
                    shader = output / (job['key'] + '.spv')
                    checked = subprocess.run([validator, '--target-env', 'vulkan1.2', str(shader)],
                                             capture_output=True, text=True, timeout=20)
                    self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                    words = struct.unpack('<' + 'I' * (shader.stat().st_size // 4), shader.read_bytes())
                    self.assertEqual(words[0], 0x07230203)
                    counts = {}
                    index = 5
                    while index < len(words):
                        count, opcode = words[index] >> 16, words[index] & 65535
                        self.assertGreater(count, 0)
                        counts[opcode] = counts.get(opcode, 0) + 1
                        index += count
                    self.assertEqual(index, len(words))
                    if job['key'].startswith('bfe_'):
                        self.assertGreater(counts.get(202, 0) + counts.get(203, 0), 0)
                    if job['key'].startswith('bfi_'):
                        self.assertGreater(counts.get(201, 0), 0)
                    if 'shf_' in job['key'] and 'dynamic' in job['key']:
                        self.assertGreaterEqual(counts.get(199, 0), 2)  # bounded word/complement counts
                    if 'immediate_zero' in job['key']:
                        self.assertEqual(sum(counts.get(i, 0) for i in (194, 195, 196)), 0)


if __name__ == '__main__':
    unittest.main()
