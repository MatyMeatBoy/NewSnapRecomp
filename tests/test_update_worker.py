"""The external updater must wait for shutdown and restart only the fixed launcher."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, skipUnless
from unittest.mock import patch

from newsnap import update_worker as worker
from newsnap.updater import UpdateError, UpdateResult


class UpdateWorkerTests(TestCase):
    def setUp(self):
        dialog = patch.object(worker, '_show_error')
        self.error_dialog = dialog.start()
        self.addCleanup(dialog.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'staging' / 'release'
        self.install = self.root / 'installed'
        self.source.mkdir(parents=True)
        self.install.mkdir()
        for folder in (self.source, self.install):
            (folder / 'NewSnapLauncher.exe').touch()
        (self.source / 'MANIFEST.json').write_text('{}')

    def job(self):
        return worker.create_job(self.source, self.install, 12345)

    def result(self, job):
        return json.loads(job.with_suffix('.result.json').read_text(encoding='utf-8'))

    def test_job_is_outside_source_with_fixed_expected_executable(self):
        job = self.job()
        self.assertEqual(job.parent, self.source.parent)
        data = json.loads(job.read_text(encoding='utf-8'))
        self.assertEqual(data['staged_folder'], str(self.source.resolve()))
        self.assertEqual(data['install_root'], str(self.install.resolve()))
        self.assertEqual(data['parent_pid'], 12345)
        self.assertEqual(data['expected_executable'], str(self.install.resolve() / 'NewSnapLauncher.exe'))
        self.assertNotEqual(job, self.job(), 'jobs must not replace another attempt')

    def test_overlap_and_invalid_parent_rejected_before_job_creation(self):
        for source, install in ((self.source, self.source), (self.source, self.source.parent),
                                (self.source.parent, self.source)):
            with self.subTest(source=source, install=install):
                with self.assertRaises(UpdateError):
                    worker.create_job(source, install, 12345)
        for pid in (0, -1, True, '12345', 1 << 32):
            with self.subTest(pid=pid), self.assertRaises(UpdateError):
                worker.create_job(self.source, self.install, pid)
        self.assertFalse(list(self.source.parent.glob('newsnap-update-*.json')))

    def test_parent_timeout_never_applies_or_restarts(self):
        job = self.job()
        with patch.object(worker, '_wait_for_parent', return_value=False) as wait, \
             patch.object(worker, 'apply_update') as apply, \
             patch.object(worker.subprocess, 'Popen') as restart:
            self.assertEqual(worker.apply_job(job), 1)
        wait.assert_called_once_with(12345, self.install.resolve() / 'NewSnapLauncher.exe', timeout=60)
        apply.assert_not_called()
        restart.assert_not_called()
        self.assertEqual(self.result(job)['status'], 'error')
        self.assertFalse(self.result(job)['applied'])
        self.error_dialog.assert_called_once()
        self.assertEqual(self.error_dialog.call_args.args[1], job.with_suffix('.result.json'))

    def test_success_applies_then_restarts_fixed_launcher_from_install_root(self):
        job = self.job()
        result = UpdateResult('0.3', 'a' * 40, ('NewSnapLauncher.exe',), ('newsnapGameData',))
        with patch.object(worker, '_wait_for_parent', return_value=True), \
             patch.object(worker, 'apply_update', return_value=result) as apply, \
             patch.object(worker.subprocess, 'Popen') as restart:
            self.assertEqual(worker.apply_job(job), 0)
        apply.assert_called_once_with(self.source.resolve(), self.install.resolve())
        self.assertEqual(restart.call_args.args, ([str(self.install.resolve() / 'NewSnapLauncher.exe')],))
        self.assertEqual(Path(restart.call_args.kwargs['cwd']), self.install.resolve())
        self.assertFalse(restart.call_args.kwargs.get('shell', False))
        self.assertEqual(restart.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')
        self.assertEqual(self.result(job)['status'], 'applied')
        self.assertEqual(self.result(job)['version'], '0.3')
        self.assertTrue(self.result(job)['applied'])
        self.error_dialog.assert_not_called()

    def test_install_failure_has_result_and_no_restart(self):
        job = self.job()
        with patch.object(worker, '_wait_for_parent', return_value=True), \
             patch.object(worker, 'apply_update', side_effect=UpdateError('copy denied')), \
             patch.object(worker.subprocess, 'Popen') as restart:
            self.assertEqual(worker.apply_job(job), 1)
        restart.assert_not_called()
        self.assertIn('copy denied', self.result(job)['error'])
        self.assertFalse(self.result(job)['applied'])
        self.assertIn('copy denied', self.error_dialog.call_args.args[0])

    def test_restart_failure_reports_that_install_already_applied(self):
        job = self.job()
        result = UpdateResult('0.3', 'a' * 40, (), ())
        with patch.object(worker, '_wait_for_parent', return_value=True), \
             patch.object(worker, 'apply_update', return_value=result), \
             patch.object(worker.subprocess, 'Popen', side_effect=OSError('restart denied')):
            self.assertEqual(worker.apply_job(job), 1)
        self.assertTrue(self.result(job)['applied'])
        self.assertIn('restart denied', self.result(job)['error'])
        self.assertIn('se instaló', self.error_dialog.call_args.args[0])
        self.assertIn('manualmente', self.error_dialog.call_args.args[0])

    def test_tampered_job_cannot_change_restart_command(self):
        for patch_data in ({'expected_executable': str(self.install / 'other.exe')},
                           {'command': ['cmd.exe', '/c', 'echo changed']},
                           {'parent_pid': 0}, {'staged_folder': 'relative/path'}):
            job = self.job()
            data = json.loads(job.read_text())
            data.update(patch_data)
            job.write_text(json.dumps(data))
            with self.subTest(patch_data=patch_data), \
                 patch.object(worker, '_wait_for_parent') as wait, \
                 patch.object(worker, 'apply_update') as apply, \
                 patch.object(worker.subprocess, 'Popen') as restart:
                self.assertEqual(worker.apply_job(job), 1)
                wait.assert_not_called()
                apply.assert_not_called()
                restart.assert_not_called()

    @skipUnless(os.name == 'nt', 'native parent-handle validation requires Windows')
    def test_native_parent_timeout_and_wrong_identity_leave_process_alive(self):
        executable = Path(getattr(sys, '_base_executable', sys.executable)).resolve()
        process = subprocess.Popen([str(executable), '-u', '-c',
                                    'import time;print("ready",flush=True);time.sleep(20)'],
                                   stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'ready')
            self.assertFalse(worker._wait_for_parent(process.pid, executable, timeout=0.01))
            self.assertIsNone(process.poll(), 'updater must not terminate a live launcher')
            with self.assertRaisesRegex(UpdateError, 'not the installed launcher'):
                worker._wait_for_parent(process.pid, self.install / 'NewSnapLauncher.exe', timeout=0.01)
            self.assertIsNone(process.poll())
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()
        self.assertTrue(worker._wait_for_parent(process.pid, executable, timeout=0.01))
