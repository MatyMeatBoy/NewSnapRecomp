"""Files verified before are recognised without reading them again; changed ones are still found (verified_files)."""
import hashlib
import json
import os
import shutil
import struct
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from newsnap import build_kit as kit
from newsnap import game_textures as G
from newsnap import hdshadows as H
from newsnap import home_state
from newsnap import launcher_settings as settings
from newsnap import maintenance as m
from newsnap import verified_files as V
from newsnap.upstream import COMMIT
from newsnap.version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES, SHADER_EPOCH
from tests.test_game_textures import archive, index, LIGHT, SHADOW
from tests.test_verified_files import aged, sha


class Reads:
    """Counts the files read whole through maintenance.digest and the receipts."""
    def __init__(self):
        self.names = []

    def __enter__(self):
        real_digest, real_receipt = m.digest, V.VerifiedFiles.digest
        reads = self

        def digest(path, cancel_event=None):
            reads.names.append(Path(path).name)
            return real_digest(path, cancel_event)

        def receipt(self, path, cancel=None, *, full=False):
            before = self.hashed
            value = real_receipt(self, path, cancel, full=full)
            if self.hashed != before:
                reads.names.append(Path(path).name)
            return value
        self.patches = [patch.object(m, 'digest', digest), patch.object(V.VerifiedFiles, 'digest', receipt)]
        for item in self.patches:
            item.start()
        return self

    def __exit__(self, *args):
        for item in self.patches:
            item.stop()


class RuntimeFixture(unittest.TestCase):
    FILES = {'newsnap.exe': b'the executable', 'SDL3.dll': b'a library', 'ac_xlate.exe': b'translator',
             'ac_xlate.id': b'translator identity', 'upscalers/license.md': b'terms'}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'GameData'
        self.data.mkdir()
        self.install(self.data, self.FILES)

    def install(self, folder, files, **extra):
        for name, content in files.items():
            aged(folder / name, content)
        marker = {'format': 1, 'game_version': '2.0.1', 'runtime_api': RUNTIME_API, 'runtime_version': VERSION,
                  'capabilities': list(RUNTIME_CAPABILITIES), 'native_executable_sha256': sha(files['newsnap.exe']),
                  'runtime_files': {name: sha(content) for name, content in files.items()}, **extra}
        (folder / 'newsnap-game.json').write_text(json.dumps(marker))
        return marker


class GameStartCheck(RuntimeFixture):
    def test_second_check_reads_no_file_and_a_changed_file_is_found(self):
        with Reads() as first:
            self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        self.assertEqual(sorted(first.names), sorted(Path(name).name for name in self.FILES))   # each one once
        self.assertTrue((self.data / V.STORE).is_file())
        with Reads() as second:
            self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        self.assertEqual(second.names, [])
        aged(self.data / 'SDL3.dll', b'A LIBRARY', seconds=30)        # same size, another time
        with Reads() as third:
            result = m.assess_runtime(self.root)
        self.assertTrue(result['needs_rebuild'])
        self.assertIn('SDL3.dll', result['reason'])
        self.assertEqual(third.names, ['SDL3.dll'])
        aged(self.data / 'SDL3.dll', b'a library', seconds=20)
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        (self.data / 'newsnap.exe').write_bytes(b'short')              # truncated
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])
        (self.data / 'newsnap.exe').unlink()
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

    def test_full_check_reads_every_file_and_finds_what_the_receipt_cannot(self):
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        path = self.data / 'ac_xlate.exe'
        moment = path.stat().st_mtime_ns
        with path.open('r+b') as stream:      # rewritten in place, size and time put back: the documented limit
            stream.write(b'TRANSLATOR')
        os.utime(path, ns=(moment, moment))
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        with Reads() as full:
            self.assertTrue(m.assess_runtime(self.root, full=True)['needs_rebuild'])
        self.assertIn('ac_xlate.exe', full.names)
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])   # the full check renewed the receipt

    def test_damaged_receipt_store_only_costs_a_read(self):
        (self.data / V.STORE).write_text('{"format": 1, "files": {"x": 3')
        with Reads() as reads:
            self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        self.assertEqual(len(reads.names), len(self.FILES))
        self.assertEqual(json.loads((self.data / V.STORE).read_text())['format'], 1)

    def test_a_receipt_never_stands_in_for_the_expected_digest(self):
        """The store holds what the file hashed to, not «it passed»: a wrong marker still fails."""
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        marker = json.loads((self.data / 'newsnap-game.json').read_text())
        marker['runtime_files']['SDL3.dll'] = sha(b'another library')
        (self.data / 'newsnap-game.json').write_text(json.dumps(marker))
        self.assertTrue(m.assess_runtime(self.root)['needs_rebuild'])

    def test_window_check_of_the_executable_reads_it_once(self):
        with Reads() as first:
            self.assertEqual(settings.validate_runtime_data(self.root)['runtime_version'], VERSION)
        self.assertEqual(first.names, ['newsnap.exe'])
        with Reads() as second:
            settings.validate_runtime_data(self.root)
        self.assertEqual(second.names, [])
        with Reads() as full:
            settings.validate_runtime_data(self.root, full=True)
        self.assertEqual(full.names, ['newsnap.exe'])
        aged(self.data / 'newsnap.exe', b'THE EXECUTABLE', seconds=30)
        with self.assertRaises(ValueError):
            settings.validate_runtime_data(self.root)


class InstallRecognition(RuntimeFixture):
    def candidate(self, files, **extra):
        folder = self.root / 'candidate'
        folder.mkdir()
        return folder, self.install(folder, files, **extra)

    def test_installed_files_are_recognised_by_the_file_that_was_hashed(self):
        new = dict(self.FILES, **{'newsnap.exe': b'new executable', 'SDL3.dll': b'new library'})
        candidate, _ = self.candidate(new)
        with Reads() as reads:
            m.install_candidate(self.root, candidate)
        installed = [name for name in reads.names if name in ('newsnap.exe', 'SDL3.dll')]
        if V.VerifiedFiles().digest and os.stat(self.data / 'newsnap.exe').st_ino:
            # candidate read whole once; the backup copy of the old file once; the installed file not again
            self.assertEqual(installed.count('newsnap.exe'), 2)
            self.assertEqual(installed.count('SDL3.dll'), 2)
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'new executable')
        stored = json.loads((self.data / V.STORE).read_text())['files']
        self.assertFalse([name for name in stored if 'candidate' in name])
        with Reads() as after:
            self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])
        self.assertEqual(after.names, [])        # the game start that follows reads nothing

    def test_file_changed_after_the_move_is_read_and_rolls_back(self):
        new = dict(self.FILES, **{'newsnap.exe': b'new executable'})
        candidate, _ = self.candidate(new)
        replace = Path.replace

        def corrupt(source, target):
            result = replace(source, target)
            if source == candidate / 'SDL3.dll':
                moment = Path(target).stat().st_mtime_ns
                Path(target).write_bytes(b'A LIBRARY')            # same size
                os.utime(target, ns=(moment + 10 ** 9, moment + 10 ** 9))
            return result
        with patch.object(Path, 'replace', corrupt):
            with self.assertRaisesRegex(ValueError, 'SDL3.dll'):
                m.install_candidate(self.root, candidate)
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'the executable')
        self.assertFalse(m.assess_runtime(self.root)['needs_rebuild'])   # restored files are read, not assumed

    def test_candidate_is_always_read_whole(self):
        new = dict(self.FILES, **{'newsnap.exe': b'new executable'})
        candidate, marker = self.candidate(new)
        receipts = V.VerifiedFiles(self.data / V.STORE)        # a receipt that claims the candidate was verified
        receipts.record(candidate / 'SDL3.dll', marker['runtime_files']['SDL3.dll'])
        receipts.entries[V.key_of(candidate / 'SDL3.dll')]['at'] = time.time() + 600
        receipts.save()
        moment = (candidate / 'SDL3.dll').stat().st_mtime_ns
        (candidate / 'SDL3.dll').write_bytes(b'A LIBRARY')
        os.utime(candidate / 'SDL3.dll', ns=(moment, moment))
        with self.assertRaisesRegex(ValueError, 'SDL3.dll'):
            m.install_candidate(self.root, candidate)
        self.assertEqual((self.data / 'SDL3.dll').read_bytes(), b'a library')


class ShadersAcrossUpdates(RuntimeFixture):
    """An update with the same translator and SHADER_EPOCH keeps the compiled shaders and asks for no preparation."""
    CACHES = {'pipeline-cache.bin': b'driver cache', 'shader-prepared.bin': b'prepared',
              'newsnap-shader-preparation.json': b'{}', 'shader-prepared-driver.txt': b'driver'}

    def update(self, files):
        folder = self.root / 'candidate'
        folder.mkdir()
        self.install(folder, files, shader_preparation_required=True)   # as maintenance._worker writes it
        report = m.install_candidate(self.root, folder)
        shutil.rmtree(folder)
        return report

    def prepared(self):
        for name, content in self.CACHES.items():
            (self.data / name).write_bytes(content)
        (self.data / 'shader-cache').mkdir(exist_ok=True)
        (self.data / 'shader-cache/shader-cache.pack').write_bytes(b'translated shaders')
        settings.clear_shader_preparation_required(self.root)

    def test_same_translator_keeps_shaders_and_needs_no_preparation(self):
        first = self.update(self.FILES)                  # no record of what the old shaders were made with
        self.assertFalse(first['shader_cache_kept'])
        self.assertTrue(settings.shader_preparation_required(self.root))
        self.assertEqual(json.loads((self.data / m.SHADER_IDENTITY).read_text()),
                         {'format': 1, 'shader_epoch': SHADER_EPOCH, 'translator': sha(b'translator identity')})
        self.prepared()
        self.assertFalse(settings.shader_preparation_required(self.root))
        second = self.update(dict(self.FILES, **{'newsnap.exe': b'the next executable'}))
        self.assertTrue(second['shader_cache_kept'])
        self.assertEqual(second['invalidated'], [])
        for name, content in self.CACHES.items():
            self.assertEqual((self.data / name).read_bytes(), content)
        self.assertEqual((self.data / 'shader-cache/shader-cache.pack').read_bytes(), b'translated shaders')
        self.assertFalse(settings.shader_preparation_required(self.root))
        self.assertEqual((self.data / 'newsnap.exe').read_bytes(), b'the next executable')

    def test_another_translator_or_epoch_starts_them_again(self):
        self.update(self.FILES)
        self.prepared()
        report = self.update(dict(self.FILES, **{'ac_xlate.id': b'another translator'}))
        self.assertFalse(report['shader_cache_kept'])
        self.assertFalse(any((self.data / name).exists() for name in m.INVALIDATED))
        self.assertTrue(settings.shader_preparation_required(self.root))
        self.prepared()
        with patch('newsnap.version.SHADER_EPOCH', SHADER_EPOCH + 1):
            report = self.update(dict(self.FILES, **{'ac_xlate.id': b'another translator'}))
        self.assertFalse(report['shader_cache_kept'])
        self.assertFalse(any((self.data / name).exists() for name in m.INVALIDATED))

    def test_preparation_required_reads_only_the_marker(self):
        with Reads() as reads:
            for _ in range(3):
                self.assertFalse(settings.shader_preparation_required(self.root))
        self.assertEqual(reads.names, [])


class KitFixture(unittest.TestCase):
    NAMES = ('python/python.exe', 'source/newsnap/maintenance.py', 'source/newsnap/build.py',
             'source/third_party/astral/tools/build_game.py', 'sdk/llvm/bin/clang.exe', 'sdk/bin/ninja.exe')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.revision = 'b' * 40
        self.cache = self.base / 'cache'
        self.kit = self.cache / f'{VERSION}-{self.revision}'
        files = {}
        for name in self.NAMES:
            aged(self.kit / name, name.encode())
            files[name] = sha(name.encode())
        (self.kit / 'build-kit.json').write_text(json.dumps({
            'format': 1, 'runtime_version': VERSION, 'runtime_api': RUNTIME_API,
            'capabilities': list(RUNTIME_CAPABILITIES), 'donor_commit': COMMIT, 'contains_game_data': False,
            'source_revision': self.revision, 'files': files}))
        self.root = self.base / 'installed'
        self.root.mkdir()
        (self.root / 'MANIFEST.json').write_text(json.dumps({'version': VERSION, 'source_revision': self.revision}))
        for item in (patch.object(kit, '_cache_root', return_value=self.cache),
                     patch.dict(os.environ, {'NEWSNAP_BUILD_KIT': ''})):
            item.start()
            self.addCleanup(item.stop)


class KitRecognition(KitFixture):
    def test_saved_kit_is_read_once_and_then_recognised(self):
        with Reads() as first:
            self.assertEqual(kit.ensure_build_kit(self.root), self.kit)
        self.assertEqual(len(first.names), len(self.NAMES))
        store = self.cache / f'.verified-{self.kit.name}.json'
        self.assertTrue(store.is_file())
        with Reads() as second:
            self.assertEqual(kit.ensure_build_kit(self.root), self.kit)
        self.assertEqual(second.names, [])
        with Reads() as rebuild:      # what maintenance.rebuild_runtime does next with the same kit
            receipts = kit.kit_receipts(self.kit)
            m.verify_build_kit(self.kit, self.root, None, receipts)
        self.assertEqual(rebuild.names, [])
        with Reads() as full:         # «Verificar / reconstruir juego»
            kit.ensure_build_kit(self.root, full=True)
        self.assertEqual(len(full.names), len(self.NAMES))

    def test_changed_added_removed_or_linked_files_are_still_found(self):
        kit.ensure_build_kit(self.root)
        tool = self.kit / 'sdk/bin/ninja.exe'
        aged(tool, b'sdk/bin/NINJA.exe', seconds=30)          # same size, another time
        with Reads() as reads:
            with self.assertRaisesRegex(ValueError, 'integrity mismatch: sdk/bin/ninja.exe'):
                kit.ensure_build_kit(self.root)
        self.assertEqual(reads.names, ['ninja.exe'])
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):   # and again: the receipt holds the real digest
            kit.ensure_build_kit(self.root)
        aged(tool, b'sdk/bin/ninja.exe', seconds=20)
        kit.ensure_build_kit(self.root)
        (self.kit / 'source/sitecustomize.py').write_bytes(b'unlisted code')
        with self.assertRaises((ValueError, kit.updater.UpdateError)):
            kit.ensure_build_kit(self.root)
        receipts = kit.kit_receipts(self.kit)
        with self.assertRaisesRegex(ValueError, 'Unlisted build kit file: source/sitecustomize.py'):
            m.verify_build_kit(self.kit, self.root, None, receipts)
        (self.kit / 'source/sitecustomize.py').unlink()
        tool.unlink()
        with self.assertRaises((FileNotFoundError, kit.updater.UpdateError)):
            kit.ensure_build_kit(self.root)
        with self.assertRaises(FileNotFoundError):
            m.verify_build_kit(self.kit, self.root, None, kit.kit_receipts(self.kit))

    def test_manifest_names_that_leave_the_kit_are_refused_with_receipts_too(self):
        manifest = json.loads((self.kit / 'build-kit.json').read_text())
        outside = aged(self.cache / 'outside.bin', b'outside')
        for name in ('../outside.bin', 'sdk/../../outside.bin', str(outside), 'sdk\\bin\\ninja.exe'):
            changed = dict(manifest, files=dict(manifest['files'], **{name: sha(b'outside')}))
            (self.kit / 'build-kit.json').write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'Unsafe build kit path', msg=name):
                m.verify_build_kit(self.kit, self.root, None, V.VerifiedFiles())

    def test_link_or_junction_inside_a_saved_kit_is_refused_in_both_modes(self):
        kit.ensure_build_kit(self.root)
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'tool.exe').write_bytes(b'not part of the kit')
        link = self.kit / 'sdk/extra'
        try:
            if os.name == 'nt':
                import _winapi
                _winapi.CreateJunction(str(outside), str(link))
            else:
                link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('links cannot be created here')
        try:
            for full in (False, True):
                with self.assertRaisesRegex(kit.updater.UpdateError, 'links or junctions'):
                    kit.ensure_build_kit(self.root, full=full)
            with self.assertRaisesRegex(ValueError, 'links are not allowed'):
                m.verify_build_kit(self.kit, self.root, None, kit.kit_receipts(self.kit))
            with self.assertRaisesRegex(ValueError, 'links are not allowed'):
                m.verify_build_kit(self.kit, self.root)
        finally:
            if os.name == 'nt':
                os.rmdir(link)
            else:
                link.unlink()

    def test_inventory_walk_matches_the_files_on_disk(self):
        (self.kit / 'empty-folder').mkdir()
        found = dict(kit._entries(self.kit))
        files = {name for name, info in found.items() if not os.path.isdir(self.kit / name)}
        self.assertEqual(files, set(self.NAMES) | {'build-kit.json'})
        self.assertIn('empty-folder', found)
        self.assertIn('source/third_party/astral/tools', found)

    def test_kits_outside_the_cache_have_no_receipts(self):
        self.assertIsNone(kit.kit_receipts(self.base / 'elsewhere' / self.kit.name))
        self.assertIsNone(kit.kit_receipts(self.cache / 'not-a-kit'))
        other = self.base / 'developer-kit'
        self.kit.rename(other)
        with patch.dict(os.environ, {'NEWSNAP_BUILD_KIT': str(other)}):
            for _ in range(2):
                with Reads() as reads:
                    kit.ensure_build_kit(self.root)
                self.assertEqual(len(reads.names), len(self.NAMES))    # an explicit kit is read whole each time
        self.assertEqual(list(self.cache.glob('.verified-*')), [])


class OwnerData(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'GameData'
        self.content = {'exefs/main': b'main module', 'exefs/sdk': b'sdk module', 'romfs/romfs.bin': b'game image'}
        for name, content in self.content.items():
            aged(self.data / name, content)
        self.profile = {'exefs_sha256': {'main': sha(b'main module'), 'sdk': sha(b'sdk module')},
                        'romfs_sha256': sha(b'game image'),
                        'verified_control': {'display_version': '2.0.1', 'save_size': 1, 'journal_size': 1}}
        item = patch.object(home_state, '_profile', return_value=self.profile)
        item.start()
        self.addCleanup(item.stop)
        home_state._EDGES.clear()

    def test_verify_reads_everything_each_time_and_later_checks_recognise_it(self):
        with Reads() as first:
            self.assertTrue(home_state.verify(self.root)['verified'])
        self.assertEqual(sorted(first.names), ['main', 'romfs.bin', 'sdk'])
        with Reads() as again:                       # the player's «Verificar datos» is always a full check
            self.assertTrue(home_state.verify(self.root)['verified'])
        self.assertEqual(sorted(again.names), ['main', 'romfs.bin', 'sdk'])
        with Reads() as rebuild:                     # what the rebuild worker does (newsnap/build.py)
            receipts = home_state.owner_receipts(self.data, self.profile)
            m.verify_owner_inputs(self.data, self.profile, receipts=receipts)
        self.assertEqual(rebuild.names, [])
        with Reads() as full:                        # «Verificar / reconstruir juego»
            m.verify_owner_inputs(self.data, self.profile, receipts=receipts, full=True)
        self.assertEqual(sorted(full.names), ['main', 'romfs.bin', 'sdk'])
        with Reads() as state:
            self.assertTrue(home_state.state(self.root)['verified'])
        self.assertEqual(state.names, [])

    def test_changed_image_is_read_again_and_refused(self):
        home_state.verify(self.root)
        aged(self.data / 'romfs/romfs.bin', b'GAME IMAGE', seconds=30)       # same size, another time
        self.assertFalse(home_state.state(self.root)['verified'])
        receipts = home_state.owner_receipts(self.data, self.profile)
        with Reads() as reads:
            with self.assertRaisesRegex(ValueError, 'RomFS'):
                m.verify_owner_inputs(self.data, self.profile, receipts=receipts)
        self.assertEqual(reads.names, ['romfs.bin'])
        with self.assertRaisesRegex(ValueError, 'RomFS'):
            home_state.verify(self.root)

    def test_receipt_of_an_earlier_launcher_counts_once_and_only_while_it_holds(self):
        # what launchers before this one left: the Home receipt alone, with no 'edges' and no receipt store
        fingerprints = home_state._fingerprints(self.data, self.profile)
        legacy = {'format': 1, 'verified_at': 123.0, 'game_version': '2.0.1', 'fingerprints': fingerprints,
                  'expected': {**self.profile['exefs_sha256'], 'romfs': self.profile['romfs_sha256']}}
        (self.data / home_state.RECEIPT).write_text(json.dumps(legacy))
        self.assertEqual(home_state.state(self.root)['verified_at'], 123.0)
        with Reads() as reads:
            receipts = home_state.owner_receipts(self.data, self.profile)
            m.verify_owner_inputs(self.data, self.profile, receipts=receipts)
        self.assertEqual(reads.names, [])
        # without a valid Home receipt nothing is assumed
        aged(self.data / 'exefs/main', b'MAIN MODULE', seconds=30)
        fresh = V.VerifiedFiles(self.root / 'other-store.json')
        with patch.object(home_state, 'VerifiedFiles', return_value=fresh):
            receipts = home_state.owner_receipts(self.data, self.profile)
        self.assertEqual(receipts.entries, {})
        with self.assertRaisesRegex(ValueError, 'ExeFS main'):
            m.verify_owner_inputs(self.data, self.profile, receipts=receipts)

    def test_large_image_replaced_with_size_and_time_restored_is_noticed_at_its_ends(self):
        with patch.object(V, 'EDGE_MINIMUM', 64), patch.object(V, 'EDGE_BYTES', 16):
            image = bytearray(os.urandom(256))
            path = aged(self.data / 'romfs/romfs.bin', bytes(image))
            self.profile['romfs_sha256'] = sha(bytes(image))
            self.assertTrue(home_state.verify(self.root)['verified'])
            self.assertIn('romfs/romfs.bin', json.loads((self.data / home_state.RECEIPT).read_text())['edges'])
            moment = path.stat().st_mtime_ns
            image[250] ^= 1
            with path.open('r+b') as stream:
                stream.write(bytes(image))
            os.utime(path, ns=(moment, moment))
            self.assertTrue(home_state.state(self.root)['verified'])      # same launcher session: ends read once
            home_state._EDGES.clear()                                    # the next time the launcher opens
            self.assertFalse(home_state.state(self.root)['verified'])


def write_marker_files(folder, names):
    for name in names:
        (folder / f'{name}.dds').write_bytes(b'hd')


class ShadowRecognition(unittest.TestCase):
    """install() with the game's decoder and the upscaler replaced by stand-ins."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name)
        tex = 0x5C156DBC
        self.levels = {
            'nx/Pack/LevelComposite/master/LC_001_A.drp': archive([(LIGHT, tex, b'L' * 40), (SHADOW, tex, b'S' * 24)]),
            'nx/Pack/LevelComposite/master/LC_002_A.drp': archive([(SHADOW, tex, b'T' * 32)]),
            'nx/Pack/LevelComposite/master/LC_003_A.drp': archive([('rock_dif.nutexb', tex, b'D' * 8)])}
        image, files = b'\0' * 64, []
        for path, blob in self.levels.items():
            files.append((path, len(image), len(blob)))
            image += blob
        (self.runtime / 'romfs').mkdir()
        (self.runtime / 'romfs/romfs.bin').write_bytes(image)
        (self.runtime / 'romfs-index.bin').write_bytes(index(files + [('readme.txt', 0, 4)]))
        self.folder = self.runtime / 'hdshadows'
        self.exports = 0
        self.read = []
        real = G.archive_members

        def members(image, offset, size):
            self.read.append(offset)
            return real(image, offset, size)

        def export(runtime, data, request, out, work, cancel=None):
            self.exports += 1
            blob = Path(request).read_bytes()
            count, position, results = struct.unpack_from('<3I', blob)[2], 12, {}
            for _ in range(count):
                ordinal, length, _size, crc, _packed, _kind = struct.unpack_from('<6I', blob, position)
                name = f'{crc:016x}'
                (Path(out) / f'{name}.png').write_bytes(b'picture')
                results[ordinal] = (1, name)
                position += 24 + length
            return results

        def generate(folder, scale=2, limit=0, report=print, cancel=None, sources=None, progress=None):
            for source in sources:
                (Path(folder) / f'{source.stem}.dds').write_bytes(b'hd')
            return (len(sources), 0, 0)
        for item in (patch.object(G, 'archive_members', members), patch.object(G, 'run_export', export),
                     patch.object(H, 'generate', generate)):
            item.start()
            self.addCleanup(item.stop)

    def install(self, **options):
        self.read.clear()
        return G.install(self.runtime, report=lambda text: None, **options)

    def test_everything_built_is_recognised_without_opening_the_image(self):
        self.assertEqual(self.install(), (3, 0, 0))
        self.assertEqual(len(self.read), 3)
        marker = json.loads((self.folder / G.MARKER).read_text())
        self.assertEqual((marker['build'], marker['textures']), (G.BUILD, 3))
        self.assertEqual(marker['image'], G.image_key(self.runtime))
        self.assertTrue(G.complete(self.folder))
        self.assertFalse((self.folder / 'src').exists())
        with patch('builtins.open', side_effect=AssertionError('the game image must not be opened')):
            self.assertEqual(self.install(), (0, 0, 0))
        self.assertEqual(self.read, [])
        self.assertFalse((self.folder / 'src').exists())
        self.assertEqual(self.exports, 2)

    def test_stopped_build_goes_on_reading_only_the_archives_that_are_left(self):
        self.assertEqual(self.install(limit=2), (2, 0, 0))            # the first level only
        self.assertFalse(G.complete(self.folder))
        state = json.loads((self.folder / G.STATE).read_text())
        self.assertEqual(state['archives'], {'nx/Pack/LevelComposite/master/LC_001_A.drp': 2,
                                             'nx/Pack/LevelComposite/master/LC_003_A.drp': 0})
        self.assertEqual(state['image'], G.image_key(self.runtime))
        seen = []
        self.read.clear()
        made = G.install(self.runtime, report=seen.append)
        self.assertEqual(made, (1, 0, 0))
        self.assertEqual(len(self.read), 1)                           # only the level that was left
        self.assertTrue(any('2 de 3 texturas' in text for text in seen), seen)
        self.assertTrue(G.complete(self.folder, G.image_key(self.runtime)))

    def test_marker_of_an_earlier_version_is_completed_with_one_reading(self):
        self.install()
        (self.folder / G.MARKER).write_text(json.dumps({'build': G.BUILD, 'textures': 3}))   # no 'image'
        state = json.loads((self.folder / G.STATE).read_text())
        del state['archives'], state['image']                         # as written before this change
        (self.folder / G.STATE).write_text(json.dumps(state))
        self.assertTrue(G.complete(self.folder))                      # the runtime and the launcher still see it
        exports = self.exports
        self.assertEqual(self.install(), (0, 0, 0))
        self.assertEqual(len(self.read), 3)                           # read once to learn what the image holds
        self.assertEqual(self.exports, exports)                       # nothing built again
        self.assertEqual(json.loads((self.folder / G.MARKER).read_text())['image'], G.image_key(self.runtime))
        self.assertEqual(self.install(), (0, 0, 0))
        self.assertEqual(self.read, [])

    def test_another_game_image_or_build_is_read_again(self):
        self.install()
        image = self.runtime / 'romfs/romfs.bin'
        image.write_bytes(image.read_bytes() + b'\0' * 4)             # another image (its size is part of the key)
        self.assertEqual(self.install(), (0, 0, 0))
        self.assertEqual(len(self.read), 3)
        self.assertEqual(self.install(), (0, 0, 0))
        self.assertEqual(self.read, [])
        with patch.object(G, 'BUILD', G.BUILD + 1):
            self.assertFalse(G.complete(self.folder))
            self.assertEqual(self.install(), (3, 0, 0))               # a new BUILD makes them again
            self.assertEqual(len(self.read), 3)

    def test_hd_files_removed_by_hand_are_made_again(self):
        self.install(limit=2)
        state = json.loads((self.folder / G.STATE).read_text())
        removed = next(name for name in state['hashes'].values() if name != '-')
        (self.folder / f'{removed}.dds').unlink()
        self.assertEqual(self.install(), (2, 0, 0))                   # the removed one and the level that was left
        self.assertEqual(len(self.read), 3)
        self.assertTrue((self.folder / f'{removed}.dds').is_file())
        self.assertTrue(G.complete(self.folder))

    def test_only_and_limit_never_use_the_shortcut_or_write_the_marker(self):
        self.assertEqual(self.install(only='LC_002'), (1, 0, 0))
        self.assertEqual(len(self.read), 1)
        self.assertFalse((self.folder / G.MARKER).exists())
        self.assertEqual(self.install(), (2, 0, 0))
        self.assertTrue(G.complete(self.folder))
        with self.assertRaisesRegex(ValueError, 'no se encontraron'):
            self.install(only='LC_999')

    def test_damaged_state_is_read_as_empty(self):
        self.install(limit=2)
        state = json.loads((self.folder / G.STATE).read_text())
        state['archives'] = {'nx/Pack/LevelComposite/master/LC_002_A.drp': 'all'}
        (self.folder / G.STATE).write_text(json.dumps(state))
        self.assertEqual(self.install(), (1, 0, 0))
        self.assertEqual(len(self.read), 3)
        (self.folder / G.STATE).write_text('{"build":')
        (self.folder / G.MARKER).unlink()
        self.assertEqual(self.install(), (3, 0, 0))


if __name__ == '__main__':
    unittest.main()
