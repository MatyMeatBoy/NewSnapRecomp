"""Run the real host input mapper with Snap defaults and explicit user bindings."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT, UPSTREAM


class SnapInputTests(unittest.TestCase):
    def test_trace_is_opt_in_once_per_frame_and_bounded(self):
        header = ROOT / 'newsnap/overlays/snap_input_trace.h'
        self.assertTrue(header.is_file(), 'bounded input trace helper is missing')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is needed for the native input fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'test.c').write_text(r'''
#include <stdint.h>
#include <string.h>
static const char *enabled;
static int lines;
const char *cfg_get(const char *name) { (void)name; return enabled; }
void rt_log(const char *format, ...) { (void)format; lines++; }
#include "snap_input_trace.h"
int main(void) {
 snap_input_trace(0,0,0,0,0,0,0);
 if (lines) return 1;
 enabled="1";
 snap_input_trace(0,0,0,0,0,0,0);
 snap_input_trace(0,0,1,0,0,0,0);
 if (lines!=1) return 2;
 snap_input_trace(0,1,1,0,0,0,0);
 if (lines!=2) return 3;
 snap_input_trace(0,2,1,0,0,0,0);
 if (lines!=2) return 4;
 snap_input_trace(0,61,1,0,0,0,0);
 if (lines!=3) return 5;
 for (uint64_t i=62;i<10000;i++) snap_input_trace(0,i,(int32_t)i,0,0,0,0);
 if (lines!=512) return 6;
 snap_input_trace(1,10000,0,0,0,0,0);
 if (lines!=513) return 7;
 return 0;
}
''', encoding='utf-8')
            exe = folder / ('trace-test.exe' if os.name == 'nt' else 'trace-test')
            subprocess.run([compiler, str(folder / 'test.c'), '-I', str(header.parent),
                            '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_mouse_photo_zoom_and_user_override(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang is needed for the native input fixture')
        text = (UPSTREAM / 'runtime/input_map.c').read_text(encoding='utf-8')
        # Before this overlay exists the same fixture reproduces the inherited bug.
        if importlib.util.find_spec('newsnap.input_adapt'):
            from newsnap.input_adapt import edits
            for before, after in edits()['runtime/input_map.c']:
                self.assertEqual(text.count(before), 1)
                text = text.replace(before, after, 1)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'input_map.c').write_text(text, encoding='utf-8')
            shutil.copyfile(UPSTREAM / 'runtime/input_map.h', folder / 'input_map.h')
            (folder / 'host.h').write_text('void rt_log(const char *, ...);\n')
            (folder / 'cfg.h').write_text('const char *cfg_get(const char *);\ndouble cfg_double(const char *);\n')
            (folder / 'test.c').write_text(r'''
#include <stdio.h>
#include <string.h>
#include "input_map.h"
static const char *custom_a;
const char *cfg_get(const char *n) { return !strcmp(n,"AC_BIND_A") ? custom_a : NULL; }
double cfg_double(const char *n) { (void)n; return 15; }
void rt_log(const char *s, ...) { (void)s; }
#define CHECK(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
 uint8_t down[KEY_COUNT]={0};
 input_map_configure(); down[KEY_MOUSE_L]=1;
 CHECK(input_map_buttons(down)==(1ull<<B_A), "left click must take photo (A)");
 down[KEY_MOUSE_L]=0; down[KEY_MOUSE_R]=1;
 CHECK(input_map_buttons(down)==(1ull<<B_ZL), "right click must zoom (ZL)");
 down[KEY_MOUSE_R]=0; down[KEY_E]=1;
 CHECK(input_map_buttons(down)==(1ull<<B_A), "keyboard A remains available");
 custom_a="key:mouse_m, pad:default"; input_map_configure();
 memset(down,0,sizeof down); down[KEY_MOUSE_L]=1;
 CHECK(!input_map_buttons(down), "explicit A binding replaces default photo key");
 down[KEY_MOUSE_L]=0; down[KEY_MOUSE_M]=1;
 CHECK(input_map_buttons(down)==(1ull<<B_A), "custom photo key survives configure");
 input_map_reset(); memset(down,0,sizeof down); down[KEY_MOUSE_L]=1;
 CHECK(input_map_buttons(down)==(1ull<<B_A), "reset restores Snap photo binding");
 int32_t stick[2];
 input_mouse_stick(0,0,1.0/60,1,stick);
 CHECK(!stick[0] && !stick[1], "stationary mouse is neutral");
 input_mouse_stick(10,-10,1.0/60,1,stick);
 CHECK(stick[0]>0 && stick[1]>0, "right/up mouse axes retain their signs");
 return 0;
}
''', encoding='utf-8')
            exe = folder / ('input-test.exe' if os.name == 'nt' else 'input-test')
            subprocess.run([compiler, str(folder / 'input_map.c'), str(folder / 'test.c'),
                            '-o', str(exe), *([] if os.name == 'nt' else ['-lm'])], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
