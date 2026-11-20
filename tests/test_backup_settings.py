import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


class BackupSettingsTests(unittest.TestCase):
    def setUp(self):
        from newsnap import backup_settings
        self.mod = backup_settings
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / 'profile'
        self.profile.mkdir()
        self.destination = self.root / 'synced'
        self.destination.mkdir()

    def test_disabled_by_default_does_not_touch_profile(self):
        with patch('newsnap.profile_backup.backup_profile') as backup:
            self.assertIsNone(self.mod.load_backup_settings(self.root))
            self.assertIsNone(self.mod.backup_after_session(self.root, self.profile))
            backup.assert_not_called()

    def test_explicit_opt_in_roundtrips_and_disable_preserves_backups(self):
        config = self.mod.save_backup_settings(self.root, self.destination, profile=self.profile)
        self.assertEqual(config['destination'], str(self.destination))
        self.assertEqual(config['keep'], 3)
        self.assertEqual(self.mod.load_backup_settings(self.root), config)
        marker = self.destination / 'old.zip'
        marker.write_bytes(b'old backup')
        self.mod.disable_backup_settings(self.root)
        self.assertIsNone(self.mod.load_backup_settings(self.root))
        self.assertEqual(marker.read_bytes(), b'old backup')

    def test_profile_descendant_cannot_be_selected(self):
        nested = self.profile / 'backups'
        nested.mkdir()
        with self.assertRaises(ValueError):
            self.mod.save_backup_settings(self.root, nested, profile=self.profile)
        self.assertIsNone(self.mod.load_backup_settings(self.root))

    def test_probe_failure_cannot_enable_setting(self):
        with patch.object(self.mod.tempfile, 'mkstemp', side_effect=PermissionError('read only')):
            with self.assertRaises(OSError):
                self.mod.save_backup_settings(self.root, self.destination, profile=self.profile)
        self.assertIsNone(self.mod.load_backup_settings(self.root))

    def test_invalid_persisted_config_is_rejected(self):
        path = self.mod.settings_path(self.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        for value in ({'format': 1, 'destination': 'relative', 'keep': 3},
                      {'format': 1, 'destination': str(self.destination), 'keep': True},
                      {'format': 9, 'destination': str(self.destination), 'keep': 3}):
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                self.mod.load_backup_settings(self.root)

    def test_large_file_backup_is_delegated_without_cloud_size_limit(self):
        self.mod.save_backup_settings(self.root, self.destination, profile=self.profile)
        report = Mock()
        with patch('newsnap.profile_backup.backup_profile', return_value=self.destination / 'snapshot.zip') as backup:
            result = self.mod.backup_after_session(self.root, self.profile, report)
        self.assertEqual(result, self.destination / 'snapshot.zip')
        backup.assert_called_once_with(self.profile, self.destination, keep=3, report=report)

    def test_failure_reports_warning_without_masking_game_result(self):
        self.mod.save_backup_settings(self.root, self.destination, profile=self.profile)
        messages = []
        with patch('newsnap.profile_backup.backup_profile', side_effect=OSError('disk full')):
            self.assertIsNone(self.mod.backup_after_session(self.root, self.profile, messages.append))
        self.assertTrue(any('disk full' in message for message in messages))

    def test_unavailable_or_malformed_settings_do_not_mask_game_exit(self):
        path = self.mod.settings_path(self.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('invalid json')
        report = Mock()
        self.assertIsNone(self.mod.backup_after_session(self.root, self.profile, report))
        report.assert_called_once()


if __name__ == '__main__':
    unittest.main()
