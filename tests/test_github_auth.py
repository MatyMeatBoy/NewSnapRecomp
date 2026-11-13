import os
import tempfile
import unittest
import uuid
from unittest.mock import patch

from newsnap import github_auth


class GitHubAuthTests(unittest.TestCase):
    def test_environment_token_wins_without_cli_or_stored_secret(self):
        with patch.dict(os.environ, {'GH_TOKEN': 'fixture_token'}, clear=True), \
             patch.object(github_auth, '_stored_token') as stored, \
             patch.object(github_auth, '_cli_token') as cli:
            self.assertEqual(github_auth.get_token(), 'fixture_token')
            stored.assert_not_called()
            cli.assert_not_called()

    def test_stored_token_precedes_optional_cli_and_rejects_headers(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(github_auth, '_stored_token', return_value='stored_fixture'), \
             patch.object(github_auth, '_cli_token') as cli:
            self.assertEqual(github_auth.get_token(), 'stored_fixture')
            cli.assert_not_called()
        with self.assertRaises(ValueError):
            github_auth.save_token('token\r\nAuthorization: another')

    @unittest.skipUnless(os.name == 'nt', 'Windows Credential Manager')
    def test_windows_roundtrip_uses_unique_synthetic_credential(self):
        target = 'NewSnapRecomp-test-' + uuid.uuid4().hex
        try:
            github_auth._write_stored('synthetic_fixture', target)
            self.assertEqual(github_auth._stored_token(target), 'synthetic_fixture')
        finally:
            github_auth._delete_stored(target)
        self.assertIsNone(github_auth._stored_token(target))
