"""Native donor-function regressions: no physical gamepad, sensor or window."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'toolchain/astral-release/Astral Chain-Setup'


def adapted(relative):
    source = (ROOT / 'third_party/astral' / relative).read_text(encoding='utf-8')
    if not os.environ.get('NEWSNAP_INPUT_BASELINE'):
        try:
            from newsnap.camera_input_adapt import edits
        except ModuleNotFoundError:
            return source  # The initial red run executes the unchanged donor.
        for old, new in edits().get(relative, []):
            if source.count(old) != 1:
                raise AssertionError((relative, old, source.count(old)))
            source = source.replace(old, new, 1)
    return source


def function(source, signature):
    start = source.index(signature)
    return source[start:source.index('\n}', start) + 2] + '\n'


class CameraInputTests(unittest.TestCase):
    def native(self, source, scenarios):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(SDK / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native camera-input regression')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'fixture.c').write_text('#include <stddef.h>\n' + source, encoding='utf-8')
            executable = root / 'fixture.exe'
            command = [compiler, str(root / 'fixture.c'), '-o', str(executable)]
            if os.name != 'nt':
                command.append('-lm')
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            for scenario in scenarios:
                with self.subTest(scenario=scenario):
                    result = subprocess.run([str(executable), scenario], capture_output=True)
                    self.assertEqual(result.returncode, 0, scenario + ': native exit ' + str(result.returncode) +
                                     result.stderr.decode(errors='replace'))

    @unittest.skipUnless(os.name == 'nt', 'deterministic native Win32 thread interleaving')
    def test_live_motion_setting_cannot_be_poisoned_by_an_older_thread_read(self):
        source = adapted('runtime/input.c')
        prelude = r'''
#include <windows.h>
#include <string.h>
static volatile LONG version=1,enabled=1,paused_id;
static HANDLE entered,resume;
static unsigned cfg_version(void){return (unsigned)InterlockedCompareExchange(&version,0,0);}
static int cfg_bool(const char *name){
 int sampled=InterlockedCompareExchange(&enabled,0,0);
 if(GetCurrentThreadId()==(DWORD)InterlockedCompareExchange(&paused_id,0,0)){
  SetEvent(entered);
  if(WaitForSingleObject(resume,5000)!=WAIT_OBJECT_0)ExitProcess(10);
 }
 return sampled;
}
'''
        main = r'''
static DWORD WINAPI older_read(void *unused){
 InterlockedExchange(&paused_id,(LONG)GetCurrentThreadId());
 input_motion_enabled();return 0;
}
int main(int argc,char **argv){
 entered=CreateEventW(NULL,TRUE,FALSE,NULL);resume=CreateEventW(NULL,TRUE,FALSE,NULL);
 HANDLE thread=CreateThread(NULL,0,older_read,NULL,0,NULL);
 if(!entered||!resume||!thread||WaitForSingleObject(entered,5000)!=WAIT_OBJECT_0)return 1;
 // The newer setting is read on a guest thread while the gyro's older read is paused.
 InterlockedExchange(&enabled,0);InterlockedExchange(&version,2);
 if(input_motion_enabled())return 2;
 SetEvent(resume);if(WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0)return 3;
 // Completion of the older read must not restore an obsolete shared cached value.
 if(input_motion_enabled())return 4;
 CloseHandle(thread);CloseHandle(entered);CloseHandle(resume);return 0;
}
'''
        self.native(prelude + function(source, 'int input_motion_enabled(') + main, ['live_setting_threads'])

    def test_actual_window_backends_number_every_capture_transition(self):
        win = adapted('runtime/input_win.c')
        sdl = adapted('runtime/input_sdl.c')
        common = r'''
#include <stdint.h>
#include <stdbool.h>
enum {CUR_REL=1};
static int allowed=1;
static int input_cursor_allowed(void){return allowed;}
static void rt_log(const char *f,...){}
'''
        windows = r'''
typedef int32_t LONG;typedef void *HWND;typedef int SRWLOCK;
typedef struct {LONG left,top,right,bottom;} RECT;typedef struct {LONG x,y;} POINT;
static LONG cur_captured,cur_active=1,cur_rel,cur_suspend,snap_capture_epoch,mouse_dx=10,mouse_dy=10;
static SRWLOCK cur_lock;
static void AcquireSRWLockExclusive(SRWLOCK *p){}static void ReleaseSRWLockExclusive(SRWLOCK *p){}
static HWND GetForegroundWindow(void){return (HWND)1;}
static int IsIconic(HWND h){return 0;}static int GetClientRect(HWND h,RECT *r){r->right=100;r->bottom=100;return 1;}
static int ClientToScreen(HWND h,POINT *p){return 1;}static void ClipCursor(RECT *r){}
static LONG InterlockedExchange(volatile LONG *p,LONG v){LONG o=*p;*p=v;return o;}
static LONG InterlockedCompareExchange(volatile LONG *p,LONG v,LONG c){LONG o=*p;if(o==c)*p=v;return o;}
static LONG InterlockedIncrement(volatile LONG *p){return ++*p;}
'''
        sdl_prelude = r'''
static void *win=(void*)1;
static int32_t focused=1,cur_rel,cur_suspend,cur_pending,captured,snap_capture_epoch,mouse_dx=10,mouse_dy=10;
static float rem_x,rem_y;
enum {SDL_WINDOW_MINIMIZED=1};
static int fail_mode;
static int SDL_GetWindowFlags(void *p){return 0;}
static int SDL_SetWindowRelativeMouseMode(void *p,int mode){return !fail_mode;}
static const char *SDL_GetError(void){return "fixture";}
static int32_t plat_xchg32(volatile int32_t *p,int32_t v){int32_t o=*p;*p=v;return o;}
static int32_t plat_cas32(volatile int32_t *p,int32_t v,int32_t c){int32_t o=*p;if(o==c)*p=v;return o;}
static int32_t plat_inc32(volatile int32_t *p){return ++*p;}
'''
        for backend, source, prelude, signature, update in (
                ('win', win, windows, 'static void cursor_update(', 'cursor_update((HWND)1)'),
                ('sdl', sdl, sdl_prelude, 'static void cursor_apply(', 'cursor_apply()')):
            epoch = (function(source, 'uint32_t ikb_capture_epoch(') if 'uint32_t ikb_capture_epoch(' in source
                     else 'static uint32_t ikb_capture_epoch(void){return 0;}\n')
            main = '''
int main(int argc,char **argv){
 UPDATE;if(ikb_capture_epoch()!=1||mouse_dx||mouse_dy)return 1;
 UPDATE;if(ikb_capture_epoch()!=1)return 2;
 allowed=0;UPDATE;if(ikb_capture_epoch()!=2)return 3;
 allowed=1;UPDATE;if(ikb_capture_epoch()!=3)return 4;
 return 0;
}
'''.replace('UPDATE', update)
            with self.subTest(backend=backend):
                self.native(common + prelude + function(source, signature) + epoch + main, [backend])

    def test_mouse_retains_only_current_capture_and_frame(self):
        source = adapted('runtime/input.c')
        mapping = (ROOT / 'third_party/astral/runtime/input_map.c').read_text(encoding='utf-8')
        # Keep the donor's sensitivity conversion, including its exact rate.
        import re
        cps = re.search(r'#define MOUSE_FULL_CPS\s+([\d.]+)', mapping).group(1)
        prelude = r'''
#include <stdint.h>
#include <math.h>
#include <string.h>
enum {STICK_MAX=32767};
static struct {uint64_t frames;} gfx_counters;
static uint64_t now=1000000000;
static uint32_t epoch;
static int captured=1,foreground=1;static int32_t mx,my;
static uint64_t plat_now_ns(void){return now;}
static int ikb_captured(void){return captured;}
static int ikb_foreground(void){return foreground;}
static uint32_t ikb_capture_epoch(void){return epoch;}
static void ikb_mouse_take(int32_t *x,int32_t *y){*x=mx;*y=my;mx=my=0;}
static float mouse_sens_get(void){return 1;}
static double cam_speed_applied(void){return 1;}
'''
        main = r'''
int main(int argc,char **argv){
 int32_t out[2];gfx_counters.frames=1;
 if(!strcmp(argv[1],"initial_rest")){
  mouse_camera(out);if(out[0]||out[1])return 7;return 0;
 }
 mx=10;mouse_camera(out);
 if(!out[0]||out[1])return 1;
 if(!strcmp(argv[1],"recapture_same_frame")){
  // Both backend transitions occurred while no guest input poll ran.
  epoch+=2;now+=1000000;mouse_camera(out);
  if(out[0]||out[1])return 2;
 }else if(!strcmp(argv[1],"same_frame_hold")){
  int32_t previous=out[0];now+=1000000;mouse_camera(out);
  if(out[0]!=previous)return 3;
 }else if(!strcmp(argv[1],"next_frame_rest")){
  gfx_counters.frames++;now+=16666667;mouse_camera(out);
  if(out[0]||out[1])return 4;
 }else if(!strcmp(argv[1],"release")){
  captured=0;mx=20;mouse_camera(out);if(out[0]||out[1]||mx)return 5;
 }else if(!strcmp(argv[1],"stalled_frame")){
  now+=101000000;mouse_camera(out);if(out[0]||out[1])return 6;
 }
 return 0;
}
'''
        self.native(prelude + 'static const double MOUSE_FULL_CPS=' + cps + ';\n' +
                    function(mapping, 'void input_mouse_stick(') + function(source, 'static void mouse_camera(') + main,
                    ['initial_rest', 'recapture_same_frame', 'same_frame_hold', 'next_frame_rest', 'release', 'stalled_frame'])

    def test_motion_off_disconnect_switch_and_failure_restart_real_fusion(self):
        source = adapted('runtime/input.c')
        fusion = (ROOT / 'third_party/astral/runtime/motion_fusion.c').read_text(encoding='utf-8')
        fusion = fusion[fusion.index('enum { MOTION_RING'):]
        header = (ROOT / 'third_party/astral/runtime/input.h').read_text(encoding='utf-8')
        state = header[header.index('typedef struct {\n    int64_t delta_ns'):header.index('MotionFusion *motion_new')]
        prelude = r'''
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <stdbool.h>
#define M_PI 3.14159265358979323846
typedef int PlatMutex;typedef int PlatOnce;
#define PLAT_ONCE_INIT 0
static void plat_mutex_init(PlatMutex *p){}
static void plat_mutex_lock(PlatMutex *p){}
static void plat_mutex_unlock(PlatMutex *p){}
static void plat_mutex_lock_shared(PlatMutex *p){}
static void plat_mutex_unlock_shared(PlatMutex *p){}
static void plat_once(PlatOnce *p,void(*f)(void*),void *a){if(!*p){*p=1;f(a);}}
static void rt_fatal(const char *f,...){abort();}
static void rt_log(const char *f,...){}
typedef uint32_t SDL_JoystickID;
typedef struct {uint32_t id;int connected;float gyro;int enabled[2];} SDL_Gamepad;
static SDL_Gamepad first={1,1,1,{0,0}},second={2,1,0,{0,0}},*pad=&first;
enum {SDL_SENSOR_GYRO,SDL_SENSOR_ACCEL,SDL_EVENT_GAMEPAD_SENSOR_UPDATE};
#define SDL_STANDARD_GRAVITY 9.80665f
static int sensor_ok,enabled=1,enable_calls,fail_data,fail_enable;static SDL_JoystickID sensor_pad;
static PlatMutex lock;static jmp_buf done;static int remaining;static uint64_t now=1000000000;
static int input_motion_enabled(void){return enabled;}
static uint64_t kern_now_ns(void){return now;}
static void plat_wait_ns(uint64_t ns){if(!remaining--)longjmp(done,1);now+=ns;}
static int SDL_GamepadConnected(SDL_Gamepad *p){return p->connected;}
static SDL_JoystickID SDL_GetGamepadID(SDL_Gamepad *p){return p->id;}
static void SDL_UpdateGamepads(void){}
static void SDL_SetEventEnabled(int event,int value){}
static int SDL_GamepadHasSensor(SDL_Gamepad *p,int sensor){return 1;}
static int SDL_SetGamepadSensorEnabled(SDL_Gamepad *p,int sensor,int value){
 if(value&&sensor==SDL_SENSOR_ACCEL&&fail_enable)return 0;
 if(value)enable_calls++;p->enabled[sensor]=value;return 1;
}
static float SDL_GetGamepadSensorDataRate(SDL_Gamepad *p,int sensor){return 250;}
static const char *SDL_GetGamepadName(SDL_Gamepad *p){return "mock; no hardware";}
static int SDL_GetGamepadSensorData(SDL_Gamepad *p,int sensor,float *out,int count){
 out[0]=sensor==SDL_SENSOR_GYRO?p->gyro:0;out[1]=sensor==SDL_SENSOR_ACCEL?SDL_STANDARD_GRAVITY:0;out[2]=0;
 return !fail_data;
}
'''
        functions = function(source, 'void input_motion_axes(') + function(source, 'static int sensors_ready(')
        if 'static void snap_motion_poll(' in source:
            functions += function(source, 'static void snap_motion_poll(')
        functions += function(source, 'static void motion_main(')
        main = r'''
static void ticks(int n){remaining=n;if(!setjmp(done))motion_main(NULL);}
static int read(MotionState *s){return motion_read(motion_global(),s,1,now);}
int main(int argc,char **argv){
 MotionState s;
 if(!strcmp(argv[1],"off_never_enables")){
  enabled=0;ticks(3);if(enable_calls||read(&s))return 1;return 0;
 }
 if(!strcmp(argv[1],"rest")){
  first.gyro=0;ticks(25);if(!read(&s)||s.gyro[0]||s.angle[0]||fabs(s.dir[0]-1)>1e-6)return 2;return 0;
 }
 if(!strcmp(argv[1],"partial_enable")){
  fail_enable=1;ticks(1);if(first.enabled[0]||first.enabled[1]||read(&s))return 12;return 0;
 }
 ticks(25);if(!read(&s)||s.angle[0]<=0)return 3;
 if(!strcmp(argv[1],"off_on")){
  enabled=0;ticks(1);if(first.enabled[0]||first.enabled[1]||read(&s))return 4;
  enabled=1;first.gyro=0;ticks(1);if(!read(&s)||s.angle[0]||fabs(s.dir[0]-1)>1e-6)return 5;
 }else if(!strcmp(argv[1],"disconnect_reconnect")){
  first.connected=0;ticks(1);if(read(&s))return 6;
  first.connected=1;first.gyro=0;ticks(1);if(!read(&s)||s.angle[0])return 7;
 }else if(!strcmp(argv[1],"switch_pad")){
  pad=&second;ticks(1);if(!read(&s)||s.angle[0]||fabs(s.dir[0]-1)>1e-6)return 8;
 }else if(!strcmp(argv[1],"same_id_reopen")){
  sensor_pad=0;sensor_ok=0;first.gyro=0;ticks(1);if(!read(&s)||s.angle[0])return 13;
 }else if(!strcmp(argv[1],"sample_failure")){
  fail_data=1;ticks(1);if(read(&s))return 9;
  fail_data=0;first.gyro=0;ticks(1);if(!read(&s)||s.angle[0])return 10;
 }else if(!strcmp(argv[1],"continuous")){
  float angle=s.angle[0];ticks(1);if(!read(&s)||s.angle[0]<=angle)return 11;
 }
 return 0;
}
'''
        self.native(prelude + state + fusion + functions + main,
                    ['off_never_enables', 'off_on', 'disconnect_reconnect', 'switch_pad', 'same_id_reopen',
                     'partial_enable', 'sample_failure', 'rest', 'continuous'])

    def test_complete_adapted_input_units_compile(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(SDK / 'llvm/bin/clang.exe')
        if not (SDK / 'runtime/deps/include/SDL3/SDL.h').is_file() or not Path(compiler).is_file():
            self.skipTest('bundled clang and SDL/Vulkan headers required for complete input syntax check')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('input.c', 'input_win.c', 'input_sdl.c', 'input_wsys.h'):
                (root / name).write_text(adapted('runtime/' + name), encoding='utf-8')
            for name in ('input.c', 'input_win.c', 'input_sdl.c'):
                with self.subTest(unit=name):
                    result = subprocess.run([compiler, '-fsyntax-only', '-I', str(root), '-I', str(ROOT / 'third_party/astral/runtime'),
                                             '-I', str(SDK / 'runtime/deps/include'), '-I', str(SDK / 'runtime/deps/include/vma'),
                                             str(root / name)], capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))

    def test_existing_pad_deadzone_keeps_rest_neutral_and_intentional_input(self):
        mapping = (ROOT / 'third_party/astral/runtime/input_map.c').read_text(encoding='utf-8')
        self.native('''
#include <stdint.h>
#include <math.h>
enum {STICK_MAX=32767};
''' + function(mapping, 'void input_pad_stick(') + '''
int main(int argc,char **argv){
 int32_t out[2];float dead[]={0,.15f,.5f};
 for(int i=0;i<3;i++){input_pad_stick(0,0,dead[i],out);if(out[0]||out[1])return 1;}
 input_pad_stick(1000,-1000,.15f,out);if(out[0]||out[1])return 2;
 input_pad_stick(32767,0,.15f,out);if(out[0]!=32767||out[1])return 3;
 input_pad_stick(0,-32767,.15f,out);if(out[0]||out[1]!=-32767)return 4;
 return 0;
}
''', ['stick_rest_and_intent'])
