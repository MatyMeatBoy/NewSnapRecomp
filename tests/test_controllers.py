"""Native SDL mapping regression and real host layout coverage (no physical pad claim)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT, UPSTREAM


class ControllerTests(unittest.TestCase):
    def test_real_host_layouts_bindings_and_stick_deadzone(self):
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(
            ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(cc).is_file() and not shutil.which(cc):
            self.skipTest('clang required')
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for name in ('input_map.c', 'input_map.h'):
                shutil.copyfile(UPSTREAM / 'runtime' / name, folder / name)
            (folder / 'host.h').write_text('void rt_log(const char *, ...);\n')
            (folder / 'cfg.h').write_text('const char *cfg_get(const char *);\ndouble cfg_double(const char *);\n')
            (folder / 'test.c').write_text(r'''
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "input_map.h"
static const char *binding;
static double dead=15;
static int left_override;
const char *cfg_get(const char *s) {
 if (!strcmp(s,"AC_BIND_A")) return binding;
 return left_override && !strcmp(s,"AC_LSTICK_DEADZONE") ? "50" : NULL;
}
double cfg_double(const char *s) { return !strcmp(s,"AC_LSTICK_DEADZONE") ? 50 : dead; }
void rt_log(const char *s, ...) { (void)s; }
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"line %d: %s\n",__LINE__,#c); return 1; } } while(0)
int main(void) {
 const int faces[3][4]={{B_B,B_A,B_Y,B_X},{B_A,B_B,B_X,B_Y},{B_A,B_B,B_Y,B_X}};
 const int common[][2]={{PAD_LSTICK,B_STICK_L},{PAD_RSTICK,B_STICK_R},{PAD_L,B_L},{PAD_R,B_R},
 {PAD_START,B_PLUS},{PAD_BACK,B_MINUS},{PAD_DPAD_LEFT,B_LEFT},{PAD_DPAD_UP,B_UP},
 {PAD_DPAD_RIGHT,B_RIGHT},{PAD_DPAD_DOWN,B_DOWN},{PAD_ZL,B_ZL},{PAD_ZR,B_ZR}};
 uint8_t p[PAD_COUNT]={0}; input_map_configure();
 CHECK(input_pad_layout_pick("auto",1,PAD_KIND_NONE)==PAD_LAYOUT_NINTENDO);
 CHECK(input_pad_layout_pick("auto",0,PAD_KIND_XBOX)==PAD_LAYOUT_XBOX);
 CHECK(input_pad_layout_pick("auto",0,PAD_KIND_PLAYSTATION)==PAD_LAYOUT_PLAYSTATION);
 CHECK(input_pad_layout_pick("auto",0,PAD_KIND_NONE)==PAD_LAYOUT_XBOX);
 CHECK(input_pad_layout_pick("nintendo",0,PAD_KIND_PLAYSTATION)==PAD_LAYOUT_NINTENDO);
 for(int l=0;l<PAD_LAYOUT_COUNT;l++) {
   for(int f=0;f<4;f++) { p[PAD_SOUTH+f]=1; CHECK(input_map_pad_buttons(p,l)==(1ull<<faces[l][f])); p[PAD_SOUTH+f]=0; }
   for(unsigned i=0;i<sizeof common/sizeof common[0];i++) {
     p[common[i][0]]=1; CHECK(input_map_pad_buttons(p,l)==(1ull<<common[i][1])); p[common[i][0]]=0;
   }
 }
 binding="key:default,pad:lpaddle1"; input_map_configure();
 for(int l=0;l<PAD_LAYOUT_COUNT;l++) {
   p[PAD_LPADDLE1]=1; CHECK(input_map_pad_buttons(p,l)==(1ull<<B_A)); p[PAD_LPADDLE1]=0;
   p[PAD_EAST]=1; CHECK(!(input_map_pad_buttons(p,l)&(1ull<<B_A))); p[PAD_EAST]=0;
 }
 binding=NULL; input_map_configure();
 int32_t out[2];
 input_pad_stick(1000,-1000,input_pad_deadzone(0),out); CHECK(!out[0]&&!out[1]);
 input_pad_stick(32767,0,.15f,out); CHECK(out[0]==32767&&!out[1]);
 input_pad_stick(-32768,0,.15f,out); CHECK(out[0]==-32767&&!out[1]);
 input_pad_stick(0,32767,.15f,out); CHECK(!out[0]&&out[1]==32767);
 input_pad_stick(0,-32768,.15f,out); CHECK(!out[0]&&out[1]==-32767);
 input_pad_stick(32767,32767,.15f,out); CHECK(out[0]>23000&&out[0]<23200&&out[0]==out[1]);
 input_pad_stick(10000,0,.15f,out); CHECK(out[0]>0&&out[0]<10000&&!out[1]);
 left_override=1; CHECK(input_pad_deadzone(0)==.5f); CHECK(fabs(input_pad_deadzone(1)-.15f)<.0001);
 dead=-10; CHECK(input_pad_deadzone(1)==0); dead=90; CHECK(input_pad_deadzone(1)==.5f);
 return 0;
}
''', encoding='utf-8')
            exe = folder / ('layouts.exe' if os.name == 'nt' else 'layouts')
            result = subprocess.run([cc, str(folder / 'input_map.c'), str(folder / 'test.c'),
                                     '-o', str(exe), *([] if os.name == 'nt' else ['-lm'])], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_loader_is_staged_before_both_scans(self):
        from newsnap.input_adapt import edits
        text = (UPSTREAM / 'runtime/input.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/input.c']:
            self.assertEqual(text.count(before), 1, before)
            text = text.replace(before, after, 1)
        self.assertEqual(text.count('snap_controller_db_load();'), 2)
        self.assertIn('snap_controller_db_load();\n    if (state == 1) test_pad_attach();', text)
        self.assertIn('snap_controller_db_load();\n    SDL_UpdateGamepads();\n    int n = 0, kind', text)

    def test_optional_database_with_real_sdl_virtual_joystick(self):
        header = ROOT / 'newsnap/overlays/snap_controller_db.h'
        self.assertTrue(header.is_file(), 'optional controller database loader missing')
        if os.name != 'nt':
            self.skipTest('bundled SDL native fixture is Windows only')
        setup = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(setup / 'llvm/bin/clang.exe')
        if not Path(cc).is_file() and not shutil.which(cc):
            self.skipTest('clang required')
        with tempfile.TemporaryDirectory(prefix='controles-ñ-') as temp:
            folder = Path(temp)
            (folder / 'test.c').write_text(r'''
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <SDL3/SDL.h>
void rt_log(const char *s, ...) { (void)s; }
#include "snap_controller_db.h"
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"line %d: %s (%s)\n",__LINE__,#c,SDL_GetError()); return 1; } } while(0)
static int load_on_thread(void *unused) { (void)unused; snap_controller_db_load(); return 0; }
int main(int argc, char **argv) {
 CHECK(SDL_Init(SDL_INIT_GAMEPAD));
 SDL_VirtualJoystickDesc desc; SDL_INIT_INTERFACE(&desc);
 desc.type=SDL_JOYSTICK_TYPE_UNKNOWN; desc.nbuttons=4; desc.naxes=2;
 desc.vendor_id=0x1209; desc.product_id=0xfeed; desc.name="Snap generic regression";
 SDL_JoystickID id=SDL_AttachVirtualJoystick(&desc); CHECK(id);
 SDL_Joystick *joy=SDL_OpenJoystick(id); CHECK(joy);
 CHECK(!SDL_IsGamepad(id));
 char guid[33], mapping[512], file[4096];
 SDL_GUIDToString(SDL_GetJoystickGUID(joy),guid,sizeof guid);
 snprintf(mapping,sizeof mapping,"%s,Snap generic,a:b0,b:b1,leftx:a0,lefty:a1,platform:Windows,\n",guid);
 snprintf(file,sizeof file,"%sgamecontrollerdb.txt",SDL_GetBasePath());
 if (strcmp(argv[1],"missing")) {
   SDL_IOStream *io=SDL_IOFromFile(file,"wb"); CHECK(io);
   const char *data=!strcmp(argv[1],"invalid") ? "invalid mapping\n" : mapping;
   CHECK(SDL_WriteIO(io,data,strlen(data))==strlen(data)); SDL_CloseIO(io);
 }
 if (!strcmp(argv[1],"override")) {
   snprintf(mapping,sizeof mapping,"\n%s,Explicit user mapping,a:b1,b:b0,leftx:a0,lefty:a1,\r\n",guid);
   CHECK(SDL_SetHint(SDL_HINT_GAMECONTROLLERCONFIG,mapping));
 }
 SDL_Thread *first=SDL_CreateThread(load_on_thread,"mapping-first",NULL);
 SDL_Thread *second=SDL_CreateThread(load_on_thread,"mapping-second",NULL);
 CHECK(first && second); SDL_WaitThread(first,NULL); SDL_WaitThread(second,NULL);
 if (!strcmp(argv[1],"missing") || !strcmp(argv[1],"invalid")) {
   CHECK(!SDL_IsGamepad(id)); SDL_Quit(); return 0;
 }
 CHECK(SDL_IsGamepad(id));
 SDL_Gamepad *pad=SDL_OpenGamepad(id); CHECK(pad);
 CHECK(SDL_SetJoystickVirtualButton(joy,!strcmp(argv[1],"override") ? 1 : 0,true));
 CHECK(SDL_SetJoystickVirtualAxis(joy,0,24000)); SDL_UpdateGamepads();
 CHECK(SDL_GetGamepadButton(pad,SDL_GAMEPAD_BUTTON_SOUTH));
 CHECK(!SDL_GetGamepadButton(pad,SDL_GAMEPAD_BUTTON_EAST));
 CHECK(SDL_GetGamepadAxis(pad,SDL_GAMEPAD_AXIS_LEFTX)==24000);
 /* A second startup path cannot replace an explicit mapping or reload edited disk data. */
 SDL_IOStream *io=SDL_IOFromFile(file,"wb"); CHECK(io);
 snprintf(mapping,sizeof mapping,"%s,Changed disk,a:b3,platform:Windows,\n",guid);
 SDL_WriteIO(io,mapping,strlen(mapping)); SDL_CloseIO(io);
 snap_controller_db_load(); SDL_UpdateGamepads();
 CHECK(SDL_GetGamepadButton(pad,SDL_GAMEPAD_BUTTON_SOUTH));
 SDL_CloseJoystick(joy); CHECK(SDL_DetachVirtualJoystick(id));
 CHECK(!SDL_GamepadConnected(pad)); SDL_CloseGamepad(pad);
 id=SDL_AttachVirtualJoystick(&desc); CHECK(id); CHECK(SDL_IsGamepad(id));
 pad=SDL_OpenGamepad(id); CHECK(pad); CHECK(SDL_GamepadConnected(pad));
 SDL_CloseGamepad(pad); SDL_DetachVirtualJoystick(id); SDL_Quit();
 return 0;
}
''', encoding='utf-8')
            exe = folder / 'controllers.exe'
            build = subprocess.run([cc, str(folder / 'test.c'), '-I', str(header.parent),
                                    '-I', str(setup / 'runtime/deps/include'),
                                    str(setup / 'runtime/deps/lib/libSDL3.dll.a'), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            shutil.copyfile(setup / 'bin/SDL3.dll', folder / 'SDL3.dll')
            env = os.environ.copy()
            env.pop('SDL_GAMECONTROLLERCONFIG', None)
            env.pop('SDL_GAMECONTROLLERCONFIG_FILE', None)
            for scenario in ('missing', 'invalid', 'valid', 'override'):
                (folder / 'gamecontrollerdb.txt').unlink(missing_ok=True)
                result = subprocess.run([str(exe), scenario], cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, scenario + ': ' + result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
