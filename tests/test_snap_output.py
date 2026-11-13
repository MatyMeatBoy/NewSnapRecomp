"""Actual display-only helper and exact staged runtime seams, without a GPU."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT, UPSTREAM


class SnapOutputTests(unittest.TestCase):
    def test_display_class_and_staged_target_scale(self):
        header = ROOT / 'newsnap/overlays/snap_output_scale.h'
        self.assertTrue(header.is_file(), 'display-only scale helper is missing')
        from newsnap.output_adapt import edits
        staged = {}
        for relative, replacements in edits().items():
            text = (UPSTREAM / relative).read_text(encoding='utf-8')
            for before, after in replacements:
                self.assertEqual(text.count(before), 1, relative + ': source seam must be exact-once')
                text = text.replace(before, after, 1)
            staged[relative] = text
        assignment = next(line.strip() for line in staged['runtime/vk_exec.c'].splitlines()
                          if 'o->scale = snap_output_target_scale' in line)
        self.assertIn('snap_output_image_scale(d, samples,', staged['runtime/vk_texture.c'])
        self.assertIn('f.vk == f.ideal', staged['runtime/vk_texture.c'])
        self.assertIn('if (scale <= 1.0f && nvn_gpu_only(k->addr))', staged['runtime/vk_texture.c'])
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            compiler = str(ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is required for native fixtures')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'cfg.h').write_text('const char *cfg_value(const char *);\n')
            (folder / 'ov.h').write_text('int ov_handheld(void);\n')
            fixture = r'''
#include <stdlib.h>
#include <string.h>
#include "snap_output_scale.h"
static const char *choice="game";
static int portable;
const char *cfg_value(const char *key) {if(strcmp(key,"AC_RENDER_SCALE"))abort();return choice;}
int ov_handheld(void) {return portable;}
static float staged_target(const nvn_texdesc *description,float scale) {
 struct {nvn_texdesc d;} value={*description},*t=&value;
 struct {float scale;unsigned samples;} image={scale,1},*img=&image;
 struct {float scale;} result,*o=&result;
 ASSIGNMENT
 return o->scale;
}
static nvn_texdesc valid(void) {
 nvn_texdesc d;memset(&d,0,sizeof d);d.flags=NVN_TEXTURE_FLAGS_DISPLAY;
 d.target=NVN_TEXTURE_TARGET_2D;d.width=1920;d.height=1080;d.depth=1;d.levels=1;d.samples=1;d.format=NVN_FORMAT_RGBA8;
 return d;
}
int main(void) {
 nvn_texdesc d=valid();
 const char *settings[]={"125","150","200"};float expected[]={1.25f,1.5f,2};
 const int formats[]={NVN_FORMAT_RGBA8,NVN_FORMAT_RGBA8_SRGB,NVN_FORMAT_BGRA8,NVN_FORMAT_BGRA8_SRGB};
 for(int mode=0;mode<2;mode++)for(int i=0;i<3;i++)for(int j=0;j<4;j++) {
  portable=mode;choice=settings[i];d=valid();d.format=formats[j];
  float got=snap_output_image_scale(&d,1,1,8192);
  if(got!=(mode?1:expected[i])) return 1;
  if(staged_target(&d,got)!=1) return 2;
  d.flags|=NVN_TEXTURE_FLAGS_COMPRESSIBLE;
  if(snap_output_image_scale(&d,1,1,8192)!=got) return 3;
 }
 portable=0;choice="200";
 for(int kind=0;kind<16;kind++) {
  d=valid();unsigned samples=1;int usable=1;
  if(kind==0)d.flags=0;
  if(kind==1)d.flags|=NVN_TEXTURE_FLAGS_IMAGE;
  if(kind==2)d.flags|=NVN_TEXTURE_FLAGS_LINEAR;
  if(kind==3)d.flags|=NVN_TEXTURE_FLAGS_SPARSE;
  if(kind==4)d.flags|=NVN_TEXTURE_FLAGS_VIDEO_DECODE;
  if(kind==5)d.target=NVN_TEXTURE_TARGET_2D_ARRAY;
  if(kind==6)d.levels=2;
  if(kind==7)samples=2;
  if(kind==8)d.width=1280;
  if(kind==9)d.depth=2;
  if(kind==10)d.format=NVN_FORMAT_RGBA8UI;
  if(kind==11)usable=0;
  if(kind==12)d.flags|=0x1000;
  if(kind==13)d.height=720;
  if(kind==14)d.samples=2;
  if(kind==15)d.depth=-1;
  if(snap_output_image_scale(&d,samples,usable,8192)!=1) return 4;
  if(kind!=7&&kind!=11&&staged_target(&d,2)!=2) return 5;
 }
 d=valid();
 if(snap_output_image_scale(&d,1,1,3839)!=1||snap_output_image_scale(&d,1,1,3840)!=2) return 6;
 const char *native[]={"game","50","75","100","250","garbage",""};
 for(unsigned i=0;i<sizeof native/sizeof native[0];i++) {
  choice=native[i];if(snap_output_image_scale(&d,1,1,8192)!=1) return 7;
 }
 d.flags=0;if(staged_target(&d,3)!=3) return 8; // normal/shadow image scale is preserved
 if(staged_target(&d,0)!=1) return 9;
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
