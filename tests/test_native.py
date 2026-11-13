import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class NativeFrameTests(unittest.TestCase):
    def test_domain_framing_accepts_valid_and_rejects_invalid_messages(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang is needed for the native framing fixture')
        with tempfile.TemporaryDirectory() as temporary:
            exe = Path(temporary) / ('ipc-test.exe' if os.name == 'nt' else 'ipc-test')
            subprocess.run([compiler, str(ROOT / 'tests/ipc_frame.c'), '-I', str(ROOT / 'newsnap/overlays'),
                            '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
