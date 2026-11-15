"""Internal resolution policy (SS-02) and exact staged runtime seams, without a GPU."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT, UPSTREAM


def _staged():
    from newsnap.output_adapt import edits
    staged = {}
    for relative, replacements in edits().items():
        text = (UPSTREAM / relative).read_text(encoding='utf-8')
        for before, after in replacements:
            if text.count(before) != 1:
                raise AssertionError(relative + ': source seam must be exact-once')
            text = text.replace(before, after, 1)
        staged[relative] = text
    return staged


class SnapOutputTests(unittest.TestCase):
    def test_staged_seams(self):
        staged = _staged()
        texture = staged['runtime/vk_texture.c']
        self.assertIn('snap_output_image_scale_ex(d, samples,', texture)
        self.assertIn('tex_mirrored(t), f.depth || f.stencil)', texture)
        self.assertIn('if (scale <= 1.0f && nvn_gpu_only(k->addr))', texture)
        self.assertLess(texture.index('static int tex_mirrored('), texture.index('snap_output_image_scale_ex(d,'))
        draw = staged['runtime/vk_exec_draw.c']
        self.assertIn('if (!skip && snap_host_scale_factor() <= 1.0f && !snap_hd_photo_scale_on()) return;', draw)
        self.assertIn('o->scale = snap_output_target_scale', staged['runtime/vk_exec.c'])

    def test_policy_native(self):
        header = ROOT / 'newsnap/overlays/snap_output_scale.h'
        assignment = next(line.strip() for line in _staged()['runtime/vk_exec.c'].splitlines()
                          if 'o->scale = snap_output_target_scale' in line)
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is required for native fixtures')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'cfg.h').write_text('const char *cfg_value(const char *);\nconst char *cfg_get(const char *);\n'
                                          'const char *cfg_upscaling(void);\n')
            (folder / 'ov.h').write_text('int ov_handheld(void);\n')
            (folder / 'host.h').write_text('void rt_log(const char *,...);\n')
            fixture = r'''
#include <stdlib.h>
#include <string.h>
#include "snap_output_scale.h"
static const char *choice="game",*mode=NULL,*upscaling="off";
static int portable;
const char *cfg_value(const char *key) {if(strcmp(key,"AC_RENDER_SCALE"))abort();return choice;}
static const char *chain_knob=NULL;
static const char *photo_knob=NULL;
static const char *hd_knob="0";
static const char *hd_shadows_knob = "0";
const char *cfg_get(const char *key) {if(!strcmp(key,"AC_HD_SHADOWS"))return hd_shadows_knob;if(!strcmp(key,"AC_HD_PHOTOS"))return hd_knob;if(!strcmp(key,"AC_SS_PHOTO"))return photo_knob;if(!strcmp(key,"AC_SS_CHAIN"))return chain_knob;if(strcmp(key,"AC_SS_MODE"))abort();return mode;}
const char *cfg_upscaling(void) {return upscaling;}
int ov_handheld(void) {return portable;}
void rt_log(const char *f,...) {(void)f;}
static int fullscreen,monitor_h=1440,window_w=1600,window_h=900;
int gfx_display_height(void) {return monitor_h;}
int gfx_cfg_fullscreen(void) {return fullscreen;}
void gfx_cfg_window_size(int *w,int *h) {*w=window_w;*h=window_h;}
static float staged_target(const nvn_texdesc *description,float scale) {
 struct {nvn_texdesc d;} value={*description},*t=&value;
 struct {float scale;unsigned samples;} image={scale,1},*img=&image;
 struct {float scale;} result,*o=&result;
 ASSIGNMENT
 return o->scale;
}
static nvn_texdesc rt(int flags) {
 nvn_texdesc d;memset(&d,0,sizeof d);d.flags=flags;
 d.target=NVN_TEXTURE_TARGET_2D;d.width=1920;d.height=1080;d.depth=1;d.levels=1;d.samples=1;d.format=NVN_FORMAT_RGBA8;
 return d;
}
static float host(const nvn_texdesc *d,unsigned samples,int usable,int mirrored,int depth) {
 return snap_output_image_scale_ex(d,samples,usable,16384,mirrored,depth);
}
int main(void) {
 const char *settings[]={"125","150","200"};float expected[]={1.25f,1.5f,2};
 /* host mode: display, compressible colour and depth targets take S, and so do their passes */
 for(int i=0;i<3;i++) {
  choice=settings[i];
  nvn_texdesc d=rt(NVN_TEXTURE_FLAGS_DISPLAY);
  if(host(&d,1,1,0,0)!=expected[i]) return 1;
  if(staged_target(&d,expected[i])!=expected[i]) return 2;
  d=rt(NVN_TEXTURE_FLAGS_COMPRESSIBLE);d.levels=4;
  if(host(&d,1,1,0,0)!=expected[i]) return 3;
  d=rt(0);d.format=NVN_FORMAT_DEPTH24_STENCIL8;
  if(host(&d,1,1,0,1)!=expected[i]) return 4;
  if(snap_host_scale_factor()!=expected[i]) return 5;
 }
 choice="200";
 for(int kind=0;kind<14;kind++) {
  nvn_texdesc d=rt(NVN_TEXTURE_FLAGS_COMPRESSIBLE);unsigned samples=1;int usable=1,mirrored=0,depth=0;
  if(kind==0)d.flags=0;                               /* plain colour: CPU content or unknown */
  if(kind==1)d.flags|=NVN_TEXTURE_FLAGS_IMAGE;        /* storage image: compute grids stay native */
  if(kind==2)d.flags|=NVN_TEXTURE_FLAGS_LINEAR;
  if(kind==3)d.flags|=NVN_TEXTURE_FLAGS_SPARSE;
  if(kind==4)d.flags|=NVN_TEXTURE_FLAGS_VIDEO_DECODE;
  if(kind==5)d.target=NVN_TEXTURE_TARGET_2D_ARRAY;
  if(kind==6)samples=2;
  if(kind==7)d.width=1080,d.height=720;               /* photo targets keep their size */
  if(kind==8)d.depth=2;
  if(kind==9)usable=0;
  if(kind==10)mirrored=1;
  if(kind==11)d.flags|=NVN_TEXTURE_FLAGS_LINEAR_RENDER_TARGET;
  if(kind==12)d.width=1000,d.height=540;            /* not 16:9 */
  if(kind==13)d.samples=4;
  if(host(&d,samples,usable,mirrored,depth)!=1) return 10+kind;
 }
 /* SS-03: the 360x240 RGBA8 picture behind each BC1 thumbnail is 3x at any setting, also handheld */
 {
  hd_knob=NULL;choice="game";
  nvn_texdesc p=rt(0);p.width=360;p.height=240;
  if(host(&p,1,1,0,0)!=3.0f) return 40;
  portable=1;if(host(&p,1,1,0,0)!=3.0f) return 41;portable=0;
  p.format=NVN_FORMAT_RGBA16F;if(host(&p,1,1,0,0)!=1) return 42;p.format=NVN_FORMAT_RGBA8;
  if(host(&p,1,1,1,0)!=1) return 43;                     /* CPU-written: native */
  p.flags=NVN_TEXTURE_FLAGS_IMAGE;if(host(&p,1,1,0,0)!=1) return 44;p.flags=0;
  hd_knob="0";if(host(&p,1,1,0,0)!=1) return 45;
  nvn_texdesc s=rt(0);s.format=NVN_FORMAT_DEPTH32F;s.width=s.height=1024;
  if(!snap_shadow_map_class(&s)) return 46;
  s.width=1920;s.height=1080;if(snap_shadow_map_class(&s)) return 47;   /* the scene depth is not a shadow map */
  if(snap_shadow_scale_parse("auto")!=2||snap_shadow_scale_parse("4")!=4||snap_shadow_scale_parse("9")!=4) return 48;
  choice="200";if(snap_shadow_scale_parse("auto")!=4) return 49;
  choice="150";if(snap_shadow_scale_parse("auto")!=3) return 50;
  hd_shadows_knob="1";if(snap_shadow_scale_parse("1")!=4) return 51;hd_shadows_knob="0";
  choice="200";
 }
 nvn_texdesc d=rt(NVN_TEXTURE_FLAGS_DISPLAY);
 if(snap_output_image_scale_ex(&d,1,1,3839,0,0)!=1||snap_output_image_scale_ex(&d,1,1,3840,0,0)!=2) return 30;
 portable=1;if(host(&d,1,1,0,0)!=1||snap_host_scale_factor()!=1) return 31;
 portable=0;upscaling="fsr3";if(host(&d,1,1,0,0)!=1) return 32;
 upscaling="off";
 const char *native[]={"game","50","75","100","400","garbage",""};
 for(unsigned i=0;i<sizeof native/sizeof native[0];i++) {choice=native[i];if(host(&d,1,1,0,0)!=1) return 33;}
 /* the 16:9 chain: 960x540 and its bloom pyramid scale, 192x108 too, unless AC_SS_CHAIN=0 */
 choice="200";
 {nvn_texdesc c=rt(NVN_TEXTURE_FLAGS_COMPRESSIBLE);c.width=960;c.height=540;c.levels=6;
  if(host(&c,1,1,0,0)!=2) return 50;
  c.width=192;c.height=108;if(host(&c,1,1,0,0)!=2) return 51;
  c.width=160;c.height=90;if(host(&c,1,1,0,0)!=1) return 52;
  c.width=1080;c.height=720;if(host(&c,1,1,0,0)!=1) return 53;
  c.width=960;c.height=540;c.flags|=NVN_TEXTURE_FLAGS_IMAGE;if(host(&c,1,1,0,0)!=1) return 54;
  c.flags=NVN_TEXTURE_FLAGS_COMPRESSIBLE;chain_knob="0";if(host(&c,1,1,0,0)!=1) return 55;
  chain_knob=NULL;}
 /* AC_SS_PHOTO=1: photo targets of plain colour scale, BC never; box read only for 8-bit RGBA/BGRA */
 choice="200";
 {nvn_texdesc c=rt(NVN_TEXTURE_FLAGS_COMPRESSIBLE);c.width=1080;c.height=720;
  if(host(&c,1,1,0,0)!=1) return 60;
  photo_knob="1";if(host(&c,1,1,0,0)!=2) return 61;
  c.width=360;c.height=240;if(host(&c,1,1,0,0)!=2) return 62;
  c.format=0x42;if(host(&c,1,1,0,0)!=1) return 63;
  photo_knob=NULL;
  if(!snap_box_read(37,4)||!snap_box_read(50,4)||snap_box_read(126,4)||snap_box_read(37,8)) return 64;}
 /* added presets and display: the monitor in full screen, the window otherwise, 1..3 */
 const char *more[]={"133","175","250","300"};float more_s[]={4.0f/3.0f,1.75f,2.5f,3};
 for(int i=0;i<4;i++){choice=more[i];if(snap_host_scale_factor()!=more_s[i]) return 34;}
 choice="display";fullscreen=1;monitor_h=1440;if(snap_host_scale_factor()!=1440.0f/1080.0f) return 35;
 d=rt(NVN_TEXTURE_FLAGS_DISPLAY);
 {float s=host(&d,1,1,0,0);if((int)(1920*s+0.5f)!=2560||(int)(1080*s+0.5f)!=1440) return 36;}
 monitor_h=2160;if(snap_host_scale_factor()!=2) return 37;
 monitor_h=720;if(snap_host_scale_factor()!=1) return 38;
 monitor_h=4320;if(snap_host_scale_factor()!=3) return 39;
 fullscreen=0;window_h=900;if(snap_host_scale_factor()!=1) return 44;
 window_h=1620;if(snap_host_scale_factor()!=1.5f) return 45;
 /* engine mode (0.2 comparison): DISPLAY only, raster scale 1 for it */
 choice="200";mode="engine";
 if(snap_host_scale_factor()!=1) return 40;
 d=rt(NVN_TEXTURE_FLAGS_DISPLAY);
 if(snap_output_image_scale(&d,1,1,8192)!=2||staged_target(&d,2)!=1) return 41;
 d=rt(NVN_TEXTURE_FLAGS_COMPRESSIBLE);
 if(snap_output_image_scale(&d,1,1,8192)!=1) return 42;
 d.flags=0;if(staged_target(&d,3)!=3||staged_target(&d,0)!=1) return 43; /* shadow scales preserved */
 return 0;
}
'''.replace('ASSIGNMENT', assignment)
            (folder / 'fixture.c').write_text(fixture, encoding='utf-8')
            executable = folder / 'output-test.exe'
            subprocess.run([compiler, str(folder / 'fixture.c'), '-I', str(folder), '-I', str(header.parent),
                            '-I', str(UPSTREAM / 'runtime'), '-o', str(executable)], check=True, capture_output=True)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
