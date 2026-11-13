"""Cancelled tooling must stop writing before callers restore previous outputs."""
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from newsnap.build import run_logged


class ProcessCleanupTests(TestCase):
    def test_stdout_failure_terminates_and_reaps_owned_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            writer = folder / 'writer.py'
            marker = folder / 'late-output'
            writer.write_text('import time, pathlib\nprint("ready", flush=True)\n'
                              'time.sleep(20)\n'
                              f'pathlib.Path({str(marker)!r}).write_text("late write")\n')
            original = subprocess.Popen
            processes = []

            class BrokenReader:
                def __init__(self, stream):
                    self.stream = stream

                def __iter__(self):
                    next(self.stream)  # prove the real producer started
                    raise OSError('log consumer failed')

                def close(self):
                    self.stream.close()

            def start(*args, **kwargs):
                process = original(*args, **kwargs)
                processes.append(process)
                process.stdout = BrokenReader(process.stdout)
                return process

            try:
                with patch('newsnap.build.subprocess.Popen', side_effect=start):
                    with self.assertRaisesRegex(OSError, 'log consumer failed'):
                        run_logged([sys.executable, writer], folder / 'run.log')
                self.assertIsNotNone(processes[0].poll(), 'writer still alive after output rollback can start')
                self.assertFalse(marker.exists())
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                        process.wait(timeout=5)
                    process.stdout.close()
