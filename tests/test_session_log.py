import hashlib
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import Mock,patch
from types import SimpleNamespace
import queue
from newsnap.session_log import runtime_identity, write_record
from newsnap.launcher import Launcher


class SessionLogTests(TestCase):
    def test_identity_is_the_actual_file_hash_and_marker_claims_stay_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            exe=folder/'newsnap.exe';exe.write_bytes(b'actual runtime')
            (folder/'newsnap-game.json').write_text(json.dumps({'runtime_version':'claimed-version',
                'native_executable_sha256':'0'*64,'runtime_source_revision':'a'*40}))
            value=runtime_identity(exe)
            self.assertEqual(value['sha256'],hashlib.sha256(b'actual runtime').hexdigest())
            self.assertFalse(value['marker_hash_matches'])
            self.assertEqual(value['marker_runtime_version'],'claimed-version')
            self.assertNotIn(str(folder),json.dumps(value))

    def test_missing_identity_is_observable_without_preventing_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            result=runtime_identity(Path(temporary)/'missing.exe')
            self.assertEqual(result['hash_status'],'unavailable')
            output=Path(temporary)/'log'
            with output.open('w') as stream:
                write_record(stream,'exit',exit_code=75)
                self.assertIn('75',output.read_text())
            self.assertIn('newsnap_launcher',output.read_text())

    def test_uppercase_marker_hash_does_not_report_a_false_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'newsnap.exe';exe.write_bytes(b'fixture')
            (root/'newsnap-game.json').write_text(json.dumps({
                'native_executable_sha256':hashlib.sha256(b'fixture').hexdigest().upper()}))
            self.assertTrue(runtime_identity(exe)['marker_hash_matches'])

    def test_real_launcher_records_actual_hash_and_observed_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            exe=root/'newsnap.exe';exe.write_bytes(b'fixture runtime')
            app=SimpleNamespace(project=root,events=queue.Queue(),process=None,_session_diagnostic_env={})
            process=Mock(pid=42);process.wait.return_value=71
            with patch('newsnap.launcher.runtime_dir',return_value=root), \
                 patch('newsnap.launcher.settings.game_environment',return_value={'AC_VK_PRESENT':'mailbox','AC_SNAP_PRESENT_TRACE':'1'}), \
                 patch('newsnap.launcher.settings.game_command',return_value=[str(exe)]), \
                 patch('newsnap.launcher.subprocess.Popen',return_value=process) as start:
                with self.assertRaises(RuntimeError):
                    Launcher._execute_game(app,root/'profile',None)
            self.assertNotIn('AC_SNAP_PRESENT_TRACE',start.call_args.kwargs['env'])
            log=next((root/'logs').glob('launcher-game-*.log')).read_text()
            self.assertIn(hashlib.sha256(b'fixture runtime').hexdigest(),log)
            self.assertIn('"exit_code": 71',log)
            self.assertIn('mailbox',log)
