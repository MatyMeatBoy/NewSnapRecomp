"""Native timer observation must never mutate the guest, including failed reads."""
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class HighFpsTests(unittest.TestCase):
    def compiler(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('clang is required for native timing fixtures')
        return compiler

    def test_rail_probe_is_read_only_and_rejects_invalid_state(self):
        source = ROOT/'newsnap/overlays/snap_high_fps.c'
        self.assertIn('void snap_rail_observe(', source.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'platform').mkdir()
            (p/'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; char rest[1024];} Cpu;\n')
            (p/'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); void rt_log(const char *,...);\n')
            (p/'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n')
            (p/'fixture.c').write_text(r'''
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "cpu.h"
static unsigned char rail[0x74],curve[0x40];static int logs,readable=1;
void snap_rail_observe(Cpu *);
uint64_t kern_now_ns(void){static uint64_t now;return ++now;}
void rt_log(const char *f,...){(void)f;logs++;}
int plat_mem_read(uint64_t a,void *out,size_t n){
 if(!readable)return 0;
 if(a==(uintptr_t)rail&&n==sizeof rail){memcpy(out,rail,n);return 1;}
 if(a==(uintptr_t)curve&&n==sizeof curve){memcpy(out,curve,n);return 1;}return 0;
}
int main(void){Cpu c,before;unsigned char saved[sizeof rail];uint64_t ptr=(uintptr_t)curve;
 memset(&c,0xa5,sizeof c);c.x[19]=(uintptr_t)rail;before=c;memcpy(rail+0x30,&ptr,8);
 for(int kind=0;kind<5;kind++){
  float progress=1,length=116;
  readable=kind!=1;if(kind==2)progress=NAN;if(kind==3)length=0;if(kind==4)length=INFINITY;
  memcpy(rail+0x70,&progress,4);memcpy(curve+0x3c,&length,4);memcpy(saved,rail,sizeof rail);
  int prev=logs;snap_rail_observe(&c);
  if(memcmp(&c,&before,sizeof c)||memcmp(saved,rail,sizeof rail))return 1;
  if(kind&&logs!=prev)return 2;
 }
 return logs!=1;
}
''')
            exe=p/'rail.exe'
            subprocess.run([self.compiler(),str(p/'fixture.c'),str(source),'-I',str(p),'-o',str(exe)],
                           check=True,capture_output=True)
            result=subprocess.run([str(exe)],env=dict(os.environ,NEWSNAP_RAIL_TRACE='1'),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_ui_probes_preserve_guest_and_reject_bad_strings(self):
        source=ROOT/'newsnap/overlays/snap_high_fps.c'
        self.assertIn('void snap_ui_state_observe(',source.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'platform').mkdir()
            (p/'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; char rest[1024];} Cpu;\n')
            (p/'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); void rt_log(const char *,...);\n')
            (p/'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n')
            (p/'fixture.c').write_text(r'''
#include <stdint.h>
#include <string.h>
#include "cpu.h"
void snap_ui_state_observe(Cpu *);void snap_ui_event_observe(Cpu *);
static unsigned char memory[256];static int logs;
uint64_t kern_now_ns(void){static uint64_t n;return ++n;}
void rt_log(const char *f,...){(void)f;logs++;}
int plat_mem_read(uint64_t a,void *out,size_t n){uint64_t base=(uintptr_t)memory;
 if(a<base||n>sizeof memory||a-base>sizeof memory-n)return 0;
 memcpy(out,memory+(a-base),n);return 1;}
int main(void){Cpu c,before;unsigned char saved[256];
 memset(&c,0xa5,sizeof c);memset(memory,0,sizeof memory);
 memory[0x10]=6;memcpy(memory+0x11,"lab",3);
 memory[0x58]=10;memcpy(memory+0x59,"Ready",5);
 uint64_t player=(uintptr_t)memory;memcpy(memory+0xc0,&player,8);
 int event=6;memcpy(memory+0xc8,&event,4);memcpy(saved,memory,256);
 c.x[0]=player;c.x[1]=(uintptr_t)(memory+0x40);before=c;snap_ui_state_observe(&c);
 if(logs!=1||memcmp(&c,&before,sizeof c)||memcmp(memory,saved,256))return 1;
 c.x[1]=(uintptr_t)(memory+0xc8);c.x[2]=(uintptr_t)(memory+0xc0);c.x[3]=(uintptr_t)(memory+0x58);
 before=c;snap_ui_event_observe(&c);
 if(logs!=2||memcmp(&c,&before,sizeof c)||memcmp(memory,saved,256))return 2;
 c.x[1]=UINT64_MAX-4;before=c;snap_ui_state_observe(&c);
 if(logs!=2||memcmp(&c,&before,sizeof c))return 3;
 memory[0x58]=0xfe;c.x[1]=(uintptr_t)(memory+0x40);snap_ui_state_observe(&c);
 if(logs!=2)return 4;
 return 0;
}
''')
            exe=p/'ui.exe'
            subprocess.run([self.compiler(),str(p/'fixture.c'),str(source),'-I',str(p),'-o',str(exe)],
                           check=True,capture_output=True)
            result=subprocess.run([str(exe)],env=dict(os.environ,NEWSNAP_UI_TRACE='1'),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_high_fps_settings_round_trip_and_reject_uncapped(self):
        from newsnap.launcher_settings import validate_settings, save_settings, load_settings
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'newsnap.ini'
            path.write_text('[other]\nsentinel = keep\n')
            for hz in ('30', '60', '90', '120', '144', 'display'):
                self.assertEqual(validate_settings({'fps': hz}), {'fps': hz})
                save_settings(path, {'fps': hz})
                self.assertEqual(load_settings(path)['fps'], hz)
                self.assertIn('sentinel = keep', path.read_text())
            for hz in ('0', '-1', '240', 'uncapped', '120.0', '121'):
                with self.subTest(hz=hz), self.assertRaises(ValueError):
                    validate_settings({'fps': hz})

    def test_actual_pacer_and_strict_parser(self):
        header = ROOT/'newsnap/overlays/snap_high_fps.h'
        self.assertTrue(header.is_file(), 'high FPS pacing contract missing')
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'fixture.c').write_text(r'''
#include "snap_high_fps.h"
int main(void){
 const char *valid[]={"30","60","90","120","144"};
 unsigned rates[]={30,60,90,120,144};
 for(int i=0;i<5;i++){
  if(snap_fps_parse(valid[i])!=rates[i])return 1;
  uint64_t cap=(uint64_t)(1e9/rates[i]+.5);
  if(snap_fps_period(1,cap)!=cap)return 2;
  if(snap_fps_period(2,cap)!=1000000000ull/30)return 3;
  if(snap_fps_period(3,cap)!=1000000000ull/20)return 4;
 }
 const char *bad[]={0,"","0","240","uncapped","120.0","121","-1","120x"," 120"};
 for(unsigned i=0;i<sizeof bad/sizeof bad[0];i++)if(snap_fps_parse(bad[i])!=60)return 5;
 const double hz[]={144,100,120,165,59.94,60,75,240,0,30,119.88}, want[]={72,100,60,82.5,59.94,60,75,60,60,60,59.94};
 for(int i=0;i<11;i++){double t=snap_fps_target("display",hz[i]);if(t<want[i]-1e-9||t>want[i]+1e-9)return 6;}
 if(snap_fps_target("144",100)!=144||snap_fps_target(0,144)!=60)return 7;
 return 0;
}
''')
            exe=p/'pacer.exe'
            subprocess.run([compiler,str(p/'fixture.c'),'-I',str(header.parent),'-o',str(exe)],
                           check=True,capture_output=True)
            self.assertEqual(subprocess.run([str(exe)]).returncode, 0)

    def test_actual_in_game_row_exposes_and_selects_all_rates(self):
        from newsnap.adapt import adapt_sources
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            source=adapt_sources(p/'source')/'runtime/ui/menu.cpp'
            text=source.read_text(encoding='utf-8');start=text.index('static void row_fps_limit() {')
            body=text[start:text.index('\n}',start)+2]
            (p/'menu.cpp').write_text(r'''
#include <cassert>
#include <cstring>
enum {UI_MENU_FPS_30,UI_MENU_FPS_60,UI_MENU_FPS_LIMIT,UI_MENU_FPS_LIMIT_DESC};
static const char *current;static int expected,rows;
const char *menu_text(int id){return id==UI_MENU_FPS_30?"30 FPS":"60 FPS";}
const char *cfg_get(const char *key){assert(!strcmp(key,"AC_FPS"));return current;}
void opt_choice_list(const char *key,int,const char *const *v,const char *const *names,int n,int,int cur){
 const char *rates[]={"30","60","90","120","144"};
 assert(!strcmp(key,"AC_FPS")&&n==5&&cur==expected);
 for(int i=0;i<n;i++)assert(!strcmp(v[i],rates[i])&&names[i]&&*names[i]);rows++;
}
'''+body+r'''
int main(){const char *rates[]={"30","60","90","120","144"};
 for(int i=0;i<5;i++){current=rates[i];expected=i;row_fps_limit();}
 current=nullptr;expected=1;row_fps_limit();current="240";row_fps_limit();return rows!=7;
}
''')
            exe=p/'menu.exe'
            subprocess.run([self.compiler(),str(p/'menu.cpp'),'-o',str(exe)],check=True,capture_output=True)
            self.assertEqual(subprocess.run([str(exe)]).returncode,0)

    def test_observer_preserves_cpu_and_timer(self):
        self.assertTrue((ROOT/'newsnap/overlays/snap_high_fps.c').is_file(), 'timer observer missing')
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'platform').mkdir()
            (p/'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; char rest[1024];} Cpu;\n')
            (p/'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); void rt_log(const char *,...);\n')
            (p/'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n')
            (p/'fixture.c').write_text(r'''
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include "cpu.h"
void snap_timer_observe(Cpu *);
static unsigned char timer[0x58];
static int readable=1, logs;
static uint64_t now;
uint64_t kern_now_ns(void){now+=16666667;return now;}
int plat_mem_read(uint64_t a,void *out,size_t n){
 if(!readable||a!=(uintptr_t)timer||n!=sizeof timer)return 0;
 memcpy(out,timer,n);return 1;
}
void rt_log(const char *f,...){char b[2048];va_list a;va_start(a,f);vsnprintf(b,sizeof b,f,a);va_end(a);logs++;}
int main(void){
 Cpu c,before;unsigned char saved[sizeof timer];
 memset(&c,0xa5,sizeof c);memset(timer,0,sizeof timer);
 c.x[19]=(uintptr_t)timer;before=c;
 for(int j=0;j<3;j++){float dt=1.f/60;unsigned mode=j==1;
  memcpy(timer+0x1c+0x18*j,&dt,4);memcpy(timer+0x18+0x18*j,&mode,4);}
 memcpy(saved,timer,sizeof timer);
 for(int i=0;i<500;i++){readable=i%3!=0;snap_timer_observe(&c);
  if(memcmp(&c,&before,sizeof c)||memcmp(timer,saved,sizeof timer))return 1;}
 return getenv("NEWSNAP_TIMER_TRACE") && !strcmp(getenv("NEWSNAP_TIMER_TRACE"),"1") ? logs<1 : logs!=0;
}
''')
            exe=p/'fixture.exe'
            subprocess.run([compiler,str(p/'fixture.c'),str(ROOT/'newsnap/overlays/snap_high_fps.c'),
                            '-I',str(p),'-o',str(exe)],check=True,capture_output=True)
            for trace in ('0', '1'):
                env=dict(os.environ, NEWSNAP_TIMER_TRACE=trace)
                result=subprocess.run([str(exe)],env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()


class LatentSyncTests(unittest.TestCase):
    def test_present_moves_to_the_middle_of_its_refresh(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('no C compiler')
        header = ROOT/'newsnap/overlays/snap_latent_sync.h'
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'fixture.c').write_text(r'''
#include "snap_latent_sync.h"
int main(void){
 double T=1e9/144; uint64_t vb=1000000000000ull;
 for(int f=0;f<2000;f++){ /* a 72 fps target with +-3 ms of jitter lands mid-refresh, two refreshes apart */
  double jitter=((f*7919)%601-300)*1e4;
  uint64_t at=vb+(uint64_t)(f*2*T+T*0.5+jitter);
  uint64_t m=snap_vblank_mid_of(at,vb,T);
  double want=vb+f*2*T+T*0.5;
  if((double)m<want-1000||(double)m>want+1000)return 1;
 }
 if(snap_vblank_mid_of(123,vb,0)!=123||snap_vblank_mid_of(123,vb,1e9)!=123)return 2;
 if(snap_vblank_mid(55,"60")!=55||snap_vblank_mid(0,"display")!=0)return 3;
 if(!snap_latent_on("display")||snap_latent_on("144")||snap_latent_on(0))return 4;
 return 0;
}
''')
            exe = p/'latent.exe'
            subprocess.run([compiler, str(p/'fixture.c'), '-I', str(header.parent), '-o', str(exe)], check=True, capture_output=True)
            self.assertEqual(subprocess.run([str(exe)]).returncode, 0)
