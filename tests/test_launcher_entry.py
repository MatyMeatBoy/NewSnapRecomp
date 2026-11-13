import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.launcher_entry import main


class LauncherEntryTests(unittest.TestCase):
    def test_shader_worker_restores_streams_before_closing_log(self):
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                before = sys.stdout, sys.stderr
                directory = Path.cwd()
                try:
                    with patch('newsnap.upstream.ROOT', Path(folder)), \
                         patch.object(sys, 'argv', ['launcher', '--prepare']), \
                         patch('newsnap.shaders.prepare_observed', side_effect=ValueError('fixture') if failure else None):
                        code = main()
                        after = sys.stdout, sys.stderr
                finally:
                    sys.stdout, sys.stderr = before
                    os.chdir(directory)
                self.assertEqual(code, int(failure))
                self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
