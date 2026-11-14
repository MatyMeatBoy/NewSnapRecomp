"""Synthetic argument contract for the opt-in Snap engine resize experiment."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class SnapSupersampleTests(unittest.TestCase):
    def test_actual_helper_preserves_cpu_except_resize_arguments(self):
        source = ROOT / 'newsnap/overlays/snap_supersample.c'
        self.assertTrue(source.is_file(), 'engine resize prototype is missing')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is required for the native fixture')
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t x[32],sp,pc,nzcv; unsigned char rest[128]; } Cpu;\n')
            (directory / 'cfg.h').write_text('const char *cfg_value(const char *);\nconst char *cfg_get(const char *);\n')
            (directory / 'host.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t base,size; uint32_t state,attr,perm,ipc,device,pad; } RtMemoryInfo;\nuint32_t mem_query(uint64_t,RtMemoryInfo *);\nvoid rt_log(const char *,...);\n')
            (directory / 'fixture.c').write_text(r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "host.h"
static const char *choice="game";
static int logs;
static unsigned char context[0xe0],resource[0x40],context_before[0xe0],resource_before[0x40];
static uint64_t context_size=sizeof context,resource_size=sizeof resource;
static unsigned context_perm=1,resource_perm=3,queries;
uint32_t mem_query(uint64_t a,RtMemoryInfo *m) {
 queries++;
 memset(m,0,sizeof *m);
 uint64_t b=(uintptr_t)context;
 if(a>=b&&a-b<context_size) {m->base=b;m->size=context_size;m->perm=context_perm;return 0;}
 b=(uintptr_t)resource;
 if(a>=b&&a-b<resource_size) {m->base=b;m->size=resource_size;m->perm=resource_perm;return 0;}
 return 1;
}
static void reset_memory(void) {
 memset(context,0xc5,sizeof context); memset(resource,0x6a,sizeof resource);
 uint64_t pointer=(uintptr_t)resource;memcpy(context+0xc8,&pointer,8);resource[0x14]=0;
 memcpy(context_before,context,sizeof context);memcpy(resource_before,resource,sizeof resource);
 context_size=sizeof context;resource_size=sizeof resource;context_perm=1;resource_perm=3;queries=0;
}
static int memory_unchanged_except_flag(void) {
 return !memcmp(context,context_before,sizeof context)&&!memcmp(resource,resource_before,0x14)&&
        !memcmp(resource+0x15,resource_before+0x15,sizeof resource-0x15);
}
const char *cfg_value(const char *key) { if(strcmp(key,"AC_RENDER_SCALE")) abort(); return choice; }
const char *cfg_get(const char *key) { if(strcmp(key,"AC_SS_MODE")) abort(); return "engine"; }
void rt_log(const char *format,...) { (void)format; logs++; }
void snap_supersample_resize(Cpu *);
static void original_resize(Cpu *c,unsigned w,unsigned h,unsigned flags) {
 if(c->x[2]!=w||c->x[3]!=h||c->x[4]!=flags) abort();
}
int main(int argc,char **argv) {
 (void)argv;
 Cpu c,before,want;
 const char *options[]={"125","150","200"};
 const unsigned widths[2][3]={{2400,2880,3840},{1280,1280,1280}};
 const unsigned heights[2][3]={{1350,1620,2160},{720,720,720}};
 for(int mode=0;mode<2;mode++) for(int i=0;i<3;i++) {
  reset_memory();
  if(!mode&&i==1) {context_size=0xd0;resource_size=0x15;} // exact end boundaries are valid
  memset(&c,0xa5,sizeof c); c.x[1]=(uintptr_t)context;c.x[2]=mode?1280:1920; c.x[3]=mode?720:1080; c.x[4]=2;
  before=c; want=c; choice=options[i]; want.x[2]=widths[mode][i];want.x[3]=heights[mode][i];want.x[4]=mode?2:7;
  snap_supersample_resize(&c);
  if(memcmp(&c,&want,sizeof c)) return 1;
  if(!memory_unchanged_except_flag()||resource[0x14]!=0||queries!=(mode?0:2)) return 10;
  original_resize(&c,widths[mode][i],heights[mode][i],mode?2:7);
  if(!mode) {c=before;snap_supersample_resize(&c);if(memcmp(&c,&want,sizeof c)||resource[0x14]!=0) return 11;}
 }
 const char *native[]={"game","50","60","70","80","90","100","75","25","250","garbage",""};
 for(unsigned i=0;i<sizeof native/sizeof native[0];i++) {
  reset_memory();memset(&c,0x5a,sizeof c); c.x[1]=(uintptr_t)context;c.x[2]=1920;c.x[3]=1080;c.x[4]=2;before=c;
  choice=native[i]; snap_supersample_resize(&c);
  if(memcmp(&c,&before,sizeof c)) return 3;
  if(queries||memcmp(context,context_before,sizeof context)||memcmp(resource,resource_before,sizeof resource)) return 12;
 }
 choice="200";
 const uint64_t invalid[][3]={{1920,720,2},{1280,1080,2},{1920,1080,0},{1920,1080,5},{1920,1080,7},{1920,1080,0x100000002ull},{0,0,2},{0x100000780ull,1080,2},{1920,0x100000438ull,2},{2400,1350,2},{3840,2160,2}};
 for(unsigned i=0;i<sizeof invalid/sizeof invalid[0];i++) {
  reset_memory();c.x[1]=(uintptr_t)context;
  memcpy(c.x+2,invalid[i],sizeof invalid[i]);before=c;snap_supersample_resize(&c);
  if(memcmp(&c,&before,sizeof c)) return 4;
  if(queries||memcmp(resource,resource_before,sizeof resource)) return 13;
 }
 // Every invalid context/resource contract must preserve both Cpu and all RAM.
 for(int kind=0;kind<12;kind++) {
  reset_memory();c.x[1]=(uintptr_t)context;c.x[2]=1920;c.x[3]=1080;c.x[4]=2;
  uint64_t pointer=(uintptr_t)resource;
  if(kind==0)c.x[1]=0;
  if(kind==1)c.x[1]=UINT64_MAX-0x40;
  if(kind==2)c.x[1]=1;
  if(kind==3)context_size=0xcf; // pointer straddles the region end
  if(kind==4)context_perm=0;
  if(kind==5)pointer=0;
  if(kind==6)pointer=UINT64_MAX-4;
  if(kind==7)pointer=1;
  if(kind==8)resource_perm=1;
  if(kind==9)resource_size=0x14;
  if(kind==10)resource[0x14]=2;
  if(kind==11)c.x[1]=UINT64_MAX-0xc8; // the eight-byte pointer would wrap
  memcpy(context+0xc8,&pointer,8);before=c;
  memcpy(context_before,context,sizeof context);memcpy(resource_before,resource,sizeof resource);
  snap_supersample_resize(&c);
  if(memcmp(&c,&before,sizeof c)||memcmp(context,context_before,sizeof context)||memcmp(resource,resource_before,sizeof resource))return 14;
 }
 if(argc>1) {
  reset_memory();c.x[1]=(uintptr_t)context;
  for(int i=0;i<1000;i++) {
   c.x[2]=i%2?1280:1920;c.x[3]=i%2?720:1080;c.x[4]=2;
   choice=options[i%3];snap_supersample_resize(&c);
  }
  if(logs!=32) return 5;
 } else if(logs) return 6;
 return 0;
}
''', encoding='utf-8')
            executable = directory / 'supersample-test.exe'
            subprocess.run([compiler, str(directory / 'fixture.c'), str(source), '-I', str(directory),
                            '-o', str(executable)], capture_output=True, check=True)
            for tracing in (False, True):
                environment = {k: v for k, v in os.environ.items() if k != 'NEWSNAP_SUPERSAMPLE_TRACE'}
                if tracing:
                    environment['NEWSNAP_SUPERSAMPLE_TRACE'] = '1'
                result = subprocess.run([str(executable)] + (['trace'] if tracing else []),
                                        capture_output=True, text=True, env=environment)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_helper_runs_before_original_verified_calls(self):
        patch = ROOT / 'patches/snap-2.0.1-supersample.txt'
        self.assertTrue(patch.is_file(), 'verified call patch is missing')
        lines = [line.split('#')[0].split() for line in patch.read_text().splitlines()
                 if line.startswith(('set ', 'site '))]
        self.assertEqual(lines, [
            ['set', 'snap_supersample', 'AC_SNAP_SUPERSAMPLE_PATCH', '1'],
            ['site', 'snap_supersample', 'main', '5d6d54', '940ed903', '@fn:snap_supersample_resize', 'aa038054', 'aa0303f5', '940ed903'],
            ['site', 'snap_supersample', 'main', '634e6c', '940d60bd', '@fn:snap_supersample_resize', 'aa038053', 'aa0303f7', '940d60bd'],
        ])

    def test_patch_guest_words_keep_post_store_dimensions_together(self):
        from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
        from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
        assembler = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
        decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        for instructions, words, pair, height in [
            ('orr x20, x2, x3, lsl #32; mov x21, x3', [0xaa038054, 0xaa0303f5], 'w20', 'w21'),
            ('orr x19, x2, x3, lsl #32; mov x23, x3', [0xaa038053, 0xaa0303f7], 'w19', 'w23'),
        ]:
            encoded, _ = assembler.asm(instructions)
            self.assertEqual(bytes(encoded), b''.join(w.to_bytes(4, 'little') for w in words))
            decoded = list(decoder.disasm(bytes(encoded), 0))
            self.assertEqual([i.mnemonic for i in decoded], ['orr', 'mov'])
            for width_value, height_value in [(1920, 1080), (2400, 1350), (2880, 1620), (3840, 2160), (1280, 720)]:
                packed = width_value | (height_value << 32)
                self.assertEqual((packed & 0xffffffff, height_value), (width_value, height_value))
            store, _ = assembler.asm(f'stp {pair}, {height}, [x8, #0x30]')
            expected_store = 0x29065514 if pair == 'w20' else 0x29065d13
            self.assertEqual(bytes(store), expected_store.to_bytes(4, 'little'))


if __name__ == '__main__':
    unittest.main()
