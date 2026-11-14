import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsnap.paths import data_dir, has_game_data


class DataDiscoveryTests(unittest.TestCase):
    def test_missing_installation_does_not_adopt_parent_data(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.inputs(base / 'GameData')
            root = base / 'missing-installation'
            self.assertFalse(has_game_data(root))
            self.assertEqual(data_dir(root), root / 'GameData')

    def inputs(self, directory):
        for name in ('exefs/main', 'exefs/sdk', 'romfs/romfs.bin'):
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic input')
        return directory

    def test_stale_absolute_selection_does_not_hide_portable_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'app'; root.mkdir()
            settings = root / 'launcher-settings.json'
            settings.write_text(json.dumps({'game_data_path': str(Path(folder) / 'old-pc')}))
            expected = self.inputs(root / 'GameData')
            original = settings.read_bytes()
            self.assertEqual(data_dir(root), expected)
            self.assertEqual(settings.read_bytes(), original)

    def test_marker_only_does_not_hide_complete_legacy_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'GameData').mkdir()
            (root / 'GameData/newsnap-game.json').write_text('{}')
            expected = self.inputs(root / 'newsnapGameData')
            self.assertEqual(data_dir(root), expected)

    def test_imports_without_marker_are_present(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); expected = self.inputs(root / 'GameData')
            self.assertTrue(has_game_data(root))
            self.assertEqual(data_dir(root), expected)

    def test_direct_root_parent_and_known_wrapper_layouts(self):
        for location in ('app', 'GameData', 'newsnapGameData',
                         'app/GameData/newsnapGameData', 'GameData/newsnapGameData'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as folder:
                base = Path(folder); root = base / 'app'; root.mkdir()
                expected = self.inputs(base / location)
                self.assertEqual(data_dir(root), expected)
                self.assertTrue(has_game_data(root))

    def test_complete_explicit_external_selection_has_priority(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); root = base / 'app'; root.mkdir()
            expected = self.inputs(base / 'selected')
            self.inputs(root / 'GameData')
            (root / 'launcher-settings.json').write_text(json.dumps({'game_data_path': str(expected)}))
            self.assertEqual(data_dir(root), expected)

    def test_missing_explicit_selection_is_inactive_without_erasing_preference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'app'; root.mkdir()
            settings = root / 'launcher-settings.json'
            settings.write_text(json.dumps({'game_data_path': str(Path(folder) / 'missing')}))
            original = settings.read_bytes()
            self.assertFalse(has_game_data(root))
            self.assertEqual(data_dir(root), root / 'GameData')
            self.assertEqual(settings.read_bytes(), original)

    def test_marker_only_assessment_fallback_remains_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); expected = root / 'newsnapGameData'; expected.mkdir()
            (expected / 'newsnap-game.json').write_text('{}')
            self.assertEqual(data_dir(root), expected)
            self.assertTrue(has_game_data(root))

    def test_ambiguity_is_deterministic_and_discovery_is_bounded_readonly(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'app'; root.mkdir()
            first = self.inputs(root / 'GameData')
            self.inputs(root / 'newsnapGameData')
            hidden = self.inputs(root / 'arbitrary/deep/GameData')
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in Path(folder).rglob('*') if p.is_file()}
            with patch.object(Path, 'rglob', side_effect=AssertionError('recursive discovery forbidden')):
                self.assertEqual(data_dir(root), first)
                self.assertTrue(has_game_data(root))
            after = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in Path(folder).rglob('*') if p.is_file()}
            self.assertEqual(after, before)
            for directory in (first, root / 'newsnapGameData'):
                (directory / 'exefs/sdk').unlink()
            with patch.object(Path, 'rglob', side_effect=AssertionError('recursive discovery forbidden')):
                self.assertFalse(has_game_data(root))
                self.assertNotEqual(data_dir(root), hidden)
            for path, state in before.items():
                if path.exists():
                    self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), state)
