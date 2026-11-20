"""Exercise the actual adapted draw gate without Vulkan or game inputs."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.output_adapt import edits
from newsnap.upstream import UPSTREAM


class DrawConfigTests(unittest.TestCase):
    def test_hd_photos_avoid_redundant_scale_queries_and_preserve_gate(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('native compiler required')
        source = (UPSTREAM / 'runtime/vk_exec_draw.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/vk_exec_draw.c']:
            self.assertEqual(source.count(before), 1)
            source = source.replace(before, after, 1)
        body = source.split('    int skip = vk_tex_mip_skip() > 0;', 1)[1].split('    int gfx =', 1)[0]
        fixture = r'''
#include <stdlib.h>
static int mip, hd, calls;
static float scale;
static int snap_hd_photo_scale_on(void) { return hd; }
static float snap_host_scale_factor(void) { calls++; return scale; }
static int gate(void) { int skip=mip;
BODY
return 1;
}
int main(void) {
 for(mip=0;mip<2;mip++) for(hd=0;hd<2;hd++) for(int s=0;s<2;s++) {
  scale=s?2.0f:1.0f; calls=0;
  if(gate() != !!(mip || hd || s)) return 1;
  if((mip || hd) && calls) return 2;
 }
 // A changed setting takes effect on the very next draw: no stale cache.
 mip=0; hd=0; scale=1; if(gate()) return 3;
 hd=1; if(!gate()) return 4;
 hd=0; scale=2; if(!gate()) return 5;
 return 0;
}
'''.replace('BODY', body.replace('return;', 'return 0;'))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / 'fixture.c').write_text(fixture, encoding='utf-8')
            exe = path / 'fixture.exe'
            subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                            str(path / 'fixture.c'), '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
