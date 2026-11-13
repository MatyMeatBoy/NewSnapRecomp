import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class LifecycleTests(unittest.TestCase):
    def test_close_waits_for_all_exit_sections(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            path = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(path) if path.exists() else None
        if not compiler:
            self.skipTest('clang is needed for the lifecycle fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            shutil.copyfile(ROOT / 'newsnap/overlays/snap_lifecycle.c', folder / 'snap_lifecycle.c')
            (folder / 'platform').mkdir()
            (folder / 'host.h').write_text('''#include <stdint.h>
typedef struct { uint64_t x[31]; } Cpu;
void rt_fatal(const char *, ...);
#define HOST_OVERRIDE(name, fn)
''')
            (folder / 'platform/platform.h').write_text('''typedef struct { int locked; } PlatMutex;
#define PLAT_MUTEX_INIT {0}
void plat_mutex_lock(PlatMutex *);
void plat_mutex_unlock(PlatMutex *);
''')
            (folder / 'test.c').write_text('''#include <stdlib.h>
#include "snap_lifecycle.c"
static int requested;
void rt_fatal(const char *s, ...) { (void)s; exit(3); }
void gfx_window_request_close(void) { requested++; }
void plat_mutex_lock(PlatMutex *m) { if (m->locked) exit(4); m->locked=1; }
void plat_mutex_unlock(PlatMutex *m) { if (!m->locked) exit(5); m->locked=0; }
int main(int argc, char **argv) {
 Cpu c={0}; (void)argv;
 if (argc>1) { snap_exit_leave(&c); return 1; }
 snap_exit_enter(&c); snap_exit_enter(&c);
 if (snap_exit_begin_close()) return 1;
 snap_exit_leave(&c); if (requested) return 1;
 snap_exit_leave(&c); if (requested!=1) return 1;
 if (!snap_exit_begin_close()) return 1;
 return 0;
}
''')
            exe = folder / ('lifecycle.exe' if os.name == 'nt' else 'lifecycle')
            subprocess.run([compiler, str(folder / 'test.c'), '-o', str(exe)], check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
            self.assertEqual(subprocess.run([str(exe), 'underflow'], capture_output=True).returncode, 3)
