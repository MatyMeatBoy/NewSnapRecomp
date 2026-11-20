"""Close tiny real build-kit ZIPs; staged imports must not publish host caches."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from newsnap import build as builder
from newsnap import translator
from tools import package_build_kit as package
from tools import fetch_upscaler_sdk as fsr, fetch_dlss as dlss


class BuildKitProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sdk = self.root / 'portable'
        self.target = self.root / 'release' / 'public-kit'
        self.recipe = 'a' * 64
        header = ('// public fixture\n// recipe sha256 ' + self.recipe + '\n').encode()
        tool = b'public NativeAOT translator fixture'
        tool_id = 'c' * 64
        files = {
            'portable/bin/ac_xlate.exe': tool,
            'portable/bin/ac_xlate.id': (tool_id + '\n').encode(),
            'profiles/translator-windows.json': json.dumps(dict(format=1, platform='windows-x64',
                size=len(tool), sha256=hashlib.sha256(tool).hexdigest(), identity=tool_id)).encode(),
            'newsnap/maintenance.py': b'# public fixture',
            'newsnap/build.py': b'# public fixture',
            'patches/public.txt': b'# public fixture',
            'profiles/runtime-shaders.json': json.dumps({
                'fsr3_spv_sha256': hashlib.sha256(header).hexdigest(),
                'fsr3_recipe_sha256': self.recipe}).encode(),
            'assets/icons/icon.txt': b'public icon fixture',
            'assets/game-fingerprints/manifest.json': b'{"public_fingerprints":true}',
            'LICENSE': b'public license', 'THIRD_PARTY_NOTICES.md': b'public notices',
            'tools/fetch_upscaler_sdk.py': b'# public fixture',
            'tools/fetch_dlss.py': b'# public fixture',
            'tools/triage_game_log.py': b'# public fixture',
            'third_party/astral/runtime/public.h': b'/* public fixture */',
            'third_party/astral/recomp/public.py': b'# public fixture',
            'third_party/astral/tools/build_game.py': b'# public fixture',
            'third_party/astral/tools/ffx_sdk.py':
                ('def recipe_hash(): return ' + repr(self.recipe) + '\n').encode(),
            'third_party/astral/LICENSE': b'public license',
            'third_party/astral/THIRD_PARTY_NOTICES.md': b'public notices',
            'third_party/recomp_achievements/LICENSE': b'public game SDK license fixture',
            'third_party/recomp_achievements/include/rl_achievements.h': b'/* public SDK fixture */',
            'build/updated/fsr3_spv.h': header,
            'build/source/toolchain/ffx-sdk/c6efa6bf7f2027b3ec94f28578bb5965eabb9e55/LICENSE.txt': b'public license',
            'portable/python/python.exe': b'public portable Python fixture',
            'portable/python/python314._pth': b'python314.zip\n.\n',
            'portable/llvm/bin/clang.exe': b'public compiler fixture',
            'portable/bin/ninja.exe': b'public Ninja fixture',
            'portable/VERSION': b'public SDK fixture',
            'portable/THIRD_PARTY_NOTICES.md': b'public SDK notices',
        }
        for relative, data in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.target.parent.mkdir()
        self.patches = [patch.object(translator, 'PIN', self.root / 'profiles/translator-windows.json'),
                        patch.object(package, 'ROOT', self.root),
                        patch.object(builder, 'ROOT', self.root),
                        patch.object(package.subprocess, 'run', return_value=SimpleNamespace(returncode=0)),
                        patch.object(package.subprocess, 'check_output', side_effect=self.git_identity)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def git_identity(self, command, *, cwd, **kwargs):
        return (package.COMMIT if Path(cwd).name == 'astral' else 'b' * 40) + '\n'

    def vendor(self, module, extras=True):
        payloads = {'include/required.h': b'public pinned header', 'LICENSE.txt': b'public vendor terms'}
        pins = {name: (len(data), hashlib.sha256(data).hexdigest()) for name, data in payloads.items()}
        cache = self.root / 'toolchain' / ('fsr-sdk-' + module.VERSION if module is fsr else 'dlss-sdk-' + module.VERSION)
        for name, data in payloads.items():
            path = cache / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if extras:
            (cache / 'include/unneeded.h').write_bytes(b'not in vendor provisioner pins')
        # Never trust or copy arbitrary local receipt additions into public ZIPs.
        (cache / 'sdk-receipt.json').write_text(json.dumps({'local_path': str(self.root)}))
        item = patch.object(module, 'FILES', pins)
        item.start()
        self.addCleanup(item.stop)
        return cache, pins

    def close(self):
        _, archive = package.package(self.sdk, destination=self.target)
        with zipfile.ZipFile(archive) as source:
            prefix = self.target.name + '/'
            return {name.removeprefix(prefix): source.read(name) for name in source.namelist()}

    def test_actual_shader_import_leaves_no_bytecode_or_absolute_producer_path_in_zip(self):
        entries = self.close()
        self.assertFalse(any('__pycache__' in name or name.endswith(('.pyc', '.pyo')) for name in entries))
        self.assertFalse(any(str(self.root).encode() in data for data in entries.values()))
        self.assertEqual(entries['sdk/precompiled/fsr3_spv.h'], (self.root / 'build/updated/fsr3_spv.h').read_bytes())
        self.assertEqual(entries['source/third_party/astral/tools/ffx_sdk.py'],
                         (self.root / 'third_party/astral/tools/ffx_sdk.py').read_bytes())
        for relative in ('assets/game-fingerprints/manifest.json', 'third_party/recomp_achievements/LICENSE',
                         'third_party/recomp_achievements/include/rl_achievements.h'):
            self.assertEqual(entries['source/' + relative], (self.root / relative).read_bytes())

    def test_only_pinned_vendor_files_and_deterministic_receipt_enter_zip(self):
        for module in (fsr, dlss):
            self.vendor(module)
        entries = self.close()
        for module, folder in ((fsr, 'fsr-sdk-' + fsr.VERSION), (dlss, 'dlss-sdk-' + dlss.VERSION)):
            prefix = 'source/toolchain/' + folder + '/'
            observed = {key.removeprefix(prefix) for key in entries if key.startswith(prefix)}
            self.assertEqual(observed, set(module.FILES) | {'sdk-receipt.json'})
            receipt = json.loads(entries[prefix + 'sdk-receipt.json'])
            expected = (json.loads(module._receipt()) if hasattr(module, '_receipt') else
                        {'version': module.VERSION, 'commit': module.COMMIT,
                         'files': {name: list(pin) for name, pin in module.FILES.items()}})
            self.assertEqual(receipt, expected)

    def test_damaged_pinned_vendor_file_prevents_archive_publication(self):
        cache, _ = self.vendor(dlss)
        (cache / 'include/required.h').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'SDK'):
            self.close()
        self.assertFalse(package.archive_path(self.target).exists())

    def test_copied_shader_helper_must_match_original_donor_bytes(self):
        copy = package._copy
        def mutate_staged_helper(source, destination):
            copy(source, destination)
            if destination == self.target / 'source/third_party/astral/tools':
                with (destination / 'ffx_sdk.py').open('ab') as output:
                    output.write(b'\n# staged-only mutation; recipe_hash stays unchanged\n')
        with patch.object(package, '_copy', side_effect=mutate_staged_helper):
            with self.assertRaisesRegex(ValueError, 'helper.*donor'):
                self.close()
        self.assertFalse(package.archive_path(self.target).exists())

    def test_old_translator_with_valid_id_rejects_package_before_staging(self):
        path = self.sdk / 'bin/ac_xlate.exe'
        path.write_bytes(b'X' * path.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'translator.*executable differs'):
            self.close()
        self.assertFalse(self.target.exists())
        self.assertFalse(package.archive_path(self.target).exists())

    def test_translator_corrupted_during_copy_prevents_archive(self):
        copy = package._copy
        def corrupt(source, destination):
            copy(source, destination)
            if destination == self.target / 'sdk/bin/ac_xlate.exe':
                destination.write_bytes(b'X' * destination.stat().st_size)
        with patch.object(package, '_copy', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'translator.*executable differs'):
                self.close()
        self.assertFalse(package.archive_path(self.target).exists())

    def test_final_tree_guard_rejects_generated_python_cache(self):
        for relative in ('source/tools/__pycache__/helper.cpython-312.pyc',
                         'source/tools/helper.pyc', 'source/tools/helper.pyo'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / relative
                path.parent.mkdir(parents=True)
                path.write_bytes(b'host bytecode fixture')
                with self.assertRaisesRegex(ValueError, 'bytecode|cache'):
                    package.verify_kit_tree(Path(temporary))


if __name__ == '__main__':
    unittest.main()
