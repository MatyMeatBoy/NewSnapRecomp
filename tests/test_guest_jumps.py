"""Native nonlocal returns must resume a live owner and discard younger scopes."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from newsnap.upstream import ROOT, UPSTREAM


class GuestJumpTests(unittest.TestCase):
    def test_native_live_nested_and_stale_checkpoints(self):
        header = ROOT / 'newsnap/overlays/snap_jump.h'
        source = ROOT / 'newsnap/overlays/snap_jump.c'
        self.assertTrue(header.is_file(), 'native guest jump checkpoint support is missing')
        self.assertTrue(source.is_file())
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is required for the native jump fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snap_jump.h"
int kern_host_track;
void rt_fatal(const char *format, ...) { fprintf(stderr,"%s\n",format); exit(86); }
typedef struct { uint64_t x[12],sp,pc; __uint128_t v[8]; } Saved;
static Saved saved, nested, second;
static int escaped, child_returned, other_cpu, host_boundary, thread_words[2];
static void save_guest(Cpu *c,Saved *s) {
 memcpy(s->x,&c->x[19],sizeof s->x);s->sp=c->sp;s->pc=c->x[30];
 memcpy(s->v,&c->v[8],sizeof s->v);c->x[0]=0;
}
static void restore_guest(Cpu *c,Saved *s,uint64_t value) {
 memcpy(&c->x[19],s->x,sizeof s->x);c->sp=s->sp;c->pc=s->pc;
 memcpy(&c->v[8],s->v,sizeof s->v);c->x[0]=value?value:1;
 snap_jump_resume(c);
}
static void younger(Cpu *c) {
 SnapJumpScope *scope __attribute__((cleanup(snap_jump_scope_cleanup)))=snap_jump_scope_enter(c);
 c->sp=0x800;c->x[30]=0x2004;c->x[0]=(uintptr_t)&nested;
 SnapJumpCheckpoint *j=snap_jump_arm(scope,c,0x2004);
 if(!plat_jmp_save(&j->native))save_guest(c,&nested);
 if(!c->x[0])restore_guest(c,&nested,7);
 if(c->x[0]!=7)exit(17);
 c->x[19]=999;c->v[8]=999;
 if(other_cpu){Cpu other={0};restore_guest(&other,&saved,3);}
 if(host_boundary)thread_words[1]=1;
 restore_guest(c,&saved,0);child_returned=1;
}
static void owner(Cpu *c,int only_save) {
 SnapJumpScope *scope __attribute__((cleanup(snap_jump_scope_cleanup)))=snap_jump_scope_enter(c);
 c->sp=0x1000;c->x[19]=71;c->v[8]=82;c->x[30]=0x1004;c->x[0]=(uintptr_t)&saved;
 SnapJumpCheckpoint *j=snap_jump_arm(scope,c,0x1004);
 if(!plat_jmp_save(&j->native)) {snap_jump_check_save(c);save_guest(c,&saved);}
 if(only_save)return;
 if(!c->x[0]) {
  c->x[30]=0x1010;c->x[0]=(uintptr_t)&second;
  SnapJumpCheckpoint *another=snap_jump_arm(scope,c,0x1010);
  if(!plat_jmp_save(&another->native)) {snap_jump_check_save(c);save_guest(c,&second);}
  if(!c->x[0])younger(c);
 }
 if(c->x[19]!=71||c->sp!=0x1000||c->v[8]!=82||child_returned)exit(12);
 if(c->pc==0x1004) {if(c->x[0]!=1)exit(18);restore_guest(c,&second,5);}
 if(c->pc!=0x1010||c->x[0]!=5)exit(19);
 escaped++;
}
int main(int argc,char **argv) {
 Cpu c={0};
 if(argc>1&&!strcmp(argv[1],"stale")) {owner(&c,1);restore_guest(&c,&saved,3);return 13;}
 if(argc>1&&!strcmp(argv[1],"othercpu")) {other_cpu=1;owner(&c,0);return 14;}
 if(argc>1&&!strcmp(argv[1],"hostboundary")) {host_boundary=1;kern_host_track=1;c.thread=thread_words;owner(&c,0);return 20;}
 if(argc>1&&!strcmp(argv[1],"trackingoff")) {host_boundary=1;kern_host_track=0;c.thread=thread_words;owner(&c,0);return 21;}
 if(argc>1&&!strcmp(argv[1],"unarmed")) {c.x[30]=0x999;c.x[0]=1;snap_jump_check_save(&c);return 15;}
 owner(&c,0);owner(&c,0);
 if(escaped!=2)return 16;
 snap_jump_clear(&c);
 return 0;
}
'''
            (folder / 'fixture.c').write_text(fixture, encoding='utf-8')
            extras = []
            if os.name == 'nt':
                # Compile the runtime's actual non-SEH Windows save/go assembly.
                text = (UPSTREAM / 'runtime/platform/win32.c').read_text(encoding='utf-8')
                assembly = text[text.index('_Static_assert(sizeof(PlatJmp)'):text.index('int plat_thread_spawn(')]
                (folder / 'platform_jump.c').write_text('#include "platform/platform.h"\n' + assembly)
                extras.append(str(folder / 'platform_jump.c'))
            exe = folder / ('jump-test.exe' if os.name == 'nt' else 'jump-test')
            command = [compiler, '-O2', str(source), str(folder / 'fixture.c'), *extras,
                       '-I', str(header.parent), '-I', str(UPSTREAM / 'runtime'), '-o', str(exe)]
            built = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            for mode, expected in ((None, 0), ('stale', 86), ('othercpu', 86), ('unarmed', 86),
                                   ('hostboundary', 86), ('trackingoff', 86)):
                with self.subTest(mode=mode):
                    run = subprocess.run([str(exe), *([mode] if mode else [])], capture_output=True, timeout=10)
                    self.assertEqual(run.returncode, expected, run.stdout + run.stderr)

    def test_generator_seams_are_exact_once(self):
        from newsnap.jump_adapt import edits
        for relative, changes in edits().items():
            text = (UPSTREAM / relative).read_text(encoding='utf-8')
            for before, after in changes:
                self.assertEqual(text.count(before), 1, relative + ': drifted jump adaptation seam')
                text = text.replace(before, after, 1)
            if relative == 'runtime/kernel.c':
                self.assertTrue('int kern_host_track = 1;' in text,
                                'jump safety must remain enabled when async preemption and diagnostics are off')

    def test_real_emitter_keeps_checkpoint_in_owner_and_rejects_unknown_redispatch(self):
        from newsnap import jump_adapt
        source = (UPSTREAM / 'recomp/gen.py').read_text(encoding='utf-8')
        for before, after in jump_adapt.edits()['recomp/gen.py']:
            source = source.replace(before, after, 1)
        before_path = list(sys.path)
        previous = sys.modules.get('snap_jumps')
        try:
            sys.path.insert(0, str(UPSTREAM / 'recomp'))
            sys.modules['snap_jumps'] = jump_adapt
            namespace = {'__file__': str(UPSTREAM / 'recomp/gen.py'), '__name__': 'jump_generator_fixture'}
            exec(compile(source, namespace['__file__'], 'exec'), namespace)
            Insn = namespace['Insn']
            instructions = [Insn('op', 'c->x[19] = 71;'), Insn('bl', target=0x2000),
                            Insn('b', target=0x3000)]
            module = SimpleNamespace(base=0x1000, lo=0x1000, hi=0x4000, name='fixture',
                                     lift=lambda address: instructions[(address - 0x1000) // 4],
                                     _snap_jump_discovery=({0x2000}, set(), set()))
            emitter = namespace['Emitter'](module, {0x1000, 0x2000, 0x3000})
            lines, _ = emitter.function(0x1000, 0x100c)
            code = '\n'.join(lines)
            self.assertIn('plat_jmp_save', code)
            self.assertIn('snap_jump_scope_enter', code)
            self.assertNotIn('musttail', code)
            self.assertNotIn('Flags F', code)
            self.assertNotIn('uint64_t x19', code)
            self.assertIn('return f_3000(c);', code)
            with patch.object(emitter, 'scan', return_value=(set(), {0x1008: 'all'})):
                with self.assertRaisesRegex(ValueError, 'unresolved redispatch'):
                    emitter.function(0x1000, 0x100c)
        finally:
            sys.path[:] = before_path
            if previous is None:
                sys.modules.pop('snap_jumps', None)
            else:
                sys.modules['snap_jumps'] = previous
