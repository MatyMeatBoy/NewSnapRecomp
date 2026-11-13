from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from newsnap.menu_adapt import edits
from newsnap.upstream import ROOT


def adapted_menu():
    text=(ROOT/'third_party/astral/runtime/ui/menu.cpp').read_text(encoding='utf-8')
    for before,after in edits()['runtime/ui/menu.cpp']:
        if text.count(before)!=1:raise AssertionError(before)
        text=text.replace(before,after)
    return text


class MenuTests(unittest.TestCase):
    def test_exact_menu_seams_remove_spatial_and_legacy_choices(self):
        text=adapted_menu()
        self.assertNotIn('"Intel XeSS"',text)
        self.assertNotIn('"AMD FSR 3"',text)
        self.assertNotIn('opt_choice("AC_UPSCALER"',text)
        self.assertNotIn('opt_slider("AC_SHARPNESS"',text)
        for control in ('AC_HDR','AC_AO','AC_COLOR_PRESET','AC_COLOR_BRIGHTNESS','AC_COLOR_CONTRAST','AC_COLOR_GAMMA','AC_COLOR_SATURATION','AC_SHADOW_SCALE','AC_CONTACT_SHADOWS','AC_PCSS'):
            self.assertNotRegex(text, r'opt_(?:choice(?:_list)?|slider|toggle)\("'+control+r'"')
        self.assertIn('"AMD FSR 3.1", "AMD FSR 4"',text)

    def test_actual_native_rows_show_fsr4_and_report_unavailable(self):
        kit=ROOT/'toolchain/astral-release/Astral Chain-Setup';compiler=kit/'llvm/bin/clang++.exe'
        if not compiler.is_file():self.skipTest('pinned C++ compiler unavailable')
        text=adapted_menu();start=text.index('static void rows_upscaling(void) {');end=text.index('\nstatic void row_gpu(',start)
        body=text[start:end]
        ids=sorted(set(re.findall(r'\bUI_[A-Z_]+\b',body)))
        definitions='\n'.join(f'#define {name} {i+1}' for i,name in enumerate(ids))
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'menu.cpp';exe=Path(temporary)/'menu.exe'
            source.write_text('''#include <cassert>
#include <cstdio>
#include <cstring>
typedef int UiTextId;
'''+definitions+'''
static int backend_rows,quality_rows,reported_unavailable;
const char *menu_text(int id){return id==UI_MENU_UPSCALING_UNAVAILABLE?"unavailable":"localized";}
const char *cfg_upscaling(void){return "fsr4";}
const char *cfg_upscaling_quality(void){return "native";}
const char *vk_dlaa_upscaler_name(void){return nullptr;}
const char *vk_dlaa_running(void){return nullptr;}
int vk_dlaa_choice_state(const char *value){assert(!strcmp(value,"fsr4"));return 2;}
int cfg_smaa(void){return 1;}
int res_scene_reduced(void){return 0;}
void res_scene_for(const char *quality,unsigned out[2]){assert(!strcmp(quality,"native"));out[0]=1920;out[1]=1080;}
void opt_disable_next(int){}
void opt_choice_list(const char *key,int,const char *const *values,const char *const *names,int count,int,int current=-1,const char *note=nullptr){
    if(!strcmp(key,"AC_UPSCALING")){
        backend_rows++;assert(count==5 && current==4 && !strcmp(values[4],"fsr4"));
        assert(!strcmp(names[0],"Original") && !strcmp(names[3],"AMD FSR 3.1") && !strcmp(names[4],"AMD FSR 4"));
        for(int i=0;i<count;i++)assert(strcmp(values[i],"xess"));
        assert(note && !strcmp(note,"unavailable"));reported_unavailable++;
    } else if(!strcmp(key,"AC_UPSCALING_QUALITY")){
        quality_rows++;assert(count==4 && current==0 && !strcmp(values[0],"native"));assert(!strcmp(names[0],"Native AA / DLAA (100%)"));
    }
}
'''+body+'''
int main(){rows_upscaling();assert(backend_rows==1 && quality_rows==1 && reported_unavailable==1);}
''',encoding='utf-8')
            result=subprocess.run([str(compiler),'-O2','-Wall','-Werror',str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            subprocess.run([str(exe)],check=True,timeout=10)


if __name__=='__main__':unittest.main()
