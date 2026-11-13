import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class LocalNameTests(unittest.TestCase):
    def test_unavailable_filter_preserves_constructor_state_and_reports_error(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            path = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(path) if path.exists() else None
        if not compiler:
            self.skipTest('clang is needed for the local-name fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            shutil.copyfile(ROOT / 'newsnap/overlays/snap_names.c', folder / 'snap_names.c')
            (folder / 'host.h').write_text('''#include <stdint.h>
typedef struct { uint64_t x[31]; } Cpu;
void rt_log(const char *, ...);
#define HOST_OVERRIDE(name, fn)
''')
            (folder / 'test.c').write_text('''#include <string.h>
#include "snap_names.c"
void rt_log(const char *s, ...) { (void)s; }
int main(void) {
 unsigned char object[0x30], before[0x30]; memset(object,0x55,sizeof object);
 object[9]=0; memcpy(before,object,sizeof object);
 Cpu c={0}; c.x[0]=(uint64_t)(uintptr_t)object;
 snap_names_filter_unavailable(&c);
 return !c.x[0] || memcmp(object,before,sizeof object);
}
''')
            exe = folder / ('names.exe' if os.name == 'nt' else 'names')
            subprocess.run([compiler, str(folder / 'test.c'), '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
