"""Native fixture for Snap's own render-level selection; no game assets required."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class SnapRenderTests(unittest.TestCase):
    def test_native_level_selection_preserves_output_and_cpu(self):
        source = ROOT / 'newsnap/overlays/snap_render.c'
        self.assertTrue(source.is_file(), 'Snap render-level helper is missing')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is needed for the native fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t x[31], sp, nzcv; } Cpu;\n')
            (folder / 'cfg.h').write_text('const char *cfg_value(const char *name);\nconst char *cfg_upscaling(void);\nconst char *cfg_upscaling_quality(void);\n')
            (folder / 'host.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t base,size; uint32_t state,attr,perm,ipc,device,pad; } RtMemoryInfo;\nuint32_t mem_query(uint64_t a,RtMemoryInfo *m);\nvoid rt_log(const char *format, ...);\n')
            (folder / 'test.c').write_text(r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "host.h"
static const char *setting="game";
static const char *backend="off", *quality="native";
const char *cfg_upscaling(void) { return backend; }
const char *cfg_upscaling_quality(void) { return quality; }
static int logs;
static uint64_t base, size;
static unsigned permissions=3;
uint32_t mem_query(uint64_t a,RtMemoryInfo *m) {
 if(a<base||a-base>=size) return 1;
 memset(m,0,sizeof *m); m->base=base; m->size=size; m->perm=permissions;
 return 0;
}
const char *cfg_value(const char *name) {
 if (strcmp(name,"AC_RENDER_SCALE")) abort();
 return setting;
}
void rt_log(const char *format, ...) { (void)format; logs++; }
void snap_render_select(Cpu *);
int main(int argc,char **argv) {
 (void)argv;
 unsigned char renderer[0x1100], before[sizeof renderer];
 Cpu c, saved;
 memset(&c,0x5a,sizeof c); memset(renderer,0xa5,sizeof renderer);
 c.x[0]=(uintptr_t)renderer; saved=c;
 base=(uintptr_t)renderer; size=sizeof renderer;
 if(argc>1) {
  uint32_t zero=0; memcpy(renderer+0xcec,&zero,4);
  for(int i=0;i<1000;i++) {
   memcpy(renderer+0xce8,&zero,4); setting=i%2?"100":"50";
   snap_render_select(&c);
  }
  return logs==64?0:7;
 }
 for(int mode=0; mode<2; mode++) {
  memcpy(renderer+0xcec,&mode,4);
  for(int level=0;level<6;level++) {
   memcpy(renderer+0xce8,&level,4); memcpy(before,renderer,sizeof renderer);
   setting="game"; snap_render_select(&c);
   if(memcmp(before,renderer,sizeof renderer)||memcmp(&c,&saved,sizeof c)) return 1;
   const char *options[]={"100","90","80","70","60","50"};
   for(uint32_t expected=0;expected<6;expected++) {
    setting=options[expected]; snap_render_select(&c);
    uint32_t result; memcpy(&result,renderer+0xce8,4);
    if(result!=expected||memcmp(renderer,before,0xce8)||memcmp(renderer+0xcec,before+0xcec,sizeof renderer-0xcec)) return 2;
    if(memcmp(&c,&saved,sizeof c)) return 3;
   }
  }
 }
 const char *supersample[]={"125","150","200"};
 for(int i=0;i<3;i++) {
  uint32_t old=5, result; memcpy(renderer+0xce8,&old,4);
  setting=supersample[i]; snap_render_select(&c); memcpy(&result,renderer+0xce8,4);
  if(result!=0||memcmp(&c,&saved,sizeof c)) return 8;
 }
 const char *invalid[]={"75","25","40","garbage"};
 const char *presets[]={"native","quality","balanced","performance"};
 const uint32_t levels[]={0,3,4,5};
 const char *backends[]={"dlss","fsr3","fsr4","auto"};
 for(int b=0;b<4;b++) {
  backend=backends[b]; quality="native"; setting="50";
  snap_render_select(&c); uint32_t result; memcpy(&result,renderer+0xce8,4);
  if(result!=0||memcmp(&c,&saved,sizeof c))return 10;
 }
 backend="dlss"; setting="game";
 for(int i=0;i<4;i++) {
  quality=presets[i]; snap_render_select(&c); uint32_t result;
  memcpy(&result,renderer+0xce8,4); if(result!=levels[i]||memcmp(&c,&saved,sizeof c))return 9;
 }
 backend="off";
 memcpy(before,renderer,sizeof renderer);
 for(int i=0;i<1000;i++) {setting=invalid[i%4]; snap_render_select(&c);}
 if(memcmp(before,renderer,sizeof renderer)||logs!=1) return 4;
 setting="100"; permissions=1; snap_render_select(&c);
 if(memcmp(before,renderer,sizeof renderer)) return 5;
 permissions=3; size=0xcef; snap_render_select(&c);
 if(memcmp(before,renderer,sizeof renderer)) return 6;
 c.x[0]=0; snap_render_select(&c);
 c.x[0]=UINT64_MAX-8; snap_render_select(&c);
 return 0;
}
''', encoding='utf-8')
            executable = folder / 'render-test.exe'
            subprocess.run([compiler, str(folder / 'test.c'), str(source), '-I', str(folder),
                            '-o', str(executable)], check=True, capture_output=True)
            result = subprocess.run([str(executable)], capture_output=True, text=True,
                                    env={k: v for k, v in os.environ.items() if k != 'NEWSNAP_RENDER_TRACE'})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            trace = subprocess.run([str(executable), 'trace'], capture_output=True, text=True,
                                   env={**os.environ, 'NEWSNAP_RENDER_TRACE': '1'})
            self.assertEqual(trace.returncode, 0, trace.stdout + trace.stderr)

    def test_patch_keeps_original_load_after_helper(self):
        patch = ROOT / 'patches/snap-2.0.1-render.txt'
        self.assertTrue(patch.is_file(), 'verified Snap render patch is missing')
        sites = [line.split('#')[0].split() for line in patch.read_text().splitlines()
                 if line.startswith('site ')]
        self.assertEqual(sites, [['site', 'snap_render', 'main', '5cc0b0', 'b94ce808',
                                 '@fn:snap_render_select', 'b94ce808']])


if __name__ == '__main__':
    unittest.main()
