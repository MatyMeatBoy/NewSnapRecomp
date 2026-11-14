"""Legacy INI/environment grades must never alter Snap's original SDR output."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.adapt import adapt_sources
from newsnap.upstream import ROOT, UPSTREAM


def function(text, signature):
    start=text.index(signature); opening=text.index('{',start); depth=1; end=opening+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]


class NeutralTests(unittest.TestCase):
    def test_actual_color_and_sharpen_consumers_ignore_legacy_overrides(self):
        compiler=os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(
            ROOT/'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):self.skipTest('clang required')
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary); source=adapt_sources(folder/'source')
            config=function((source/'runtime/cfg.c').read_text(), 'const char *cfg_value(')
            color=function((UPSTREAM/'runtime/vk_color.c').read_text(), 'static int adjusting(')
            sharp=function((UPSTREAM/'runtime/vk_fsr.c').read_text(), 'static int sharpness(')
            rcas=function((UPSTREAM/'runtime/vk_fsr.c').read_text(), 'int vk_fsr_rcas_on(')
            fixture=folder/'neutral.c'
            fixture.write_text('''#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "snap_neutral.h"
typedef struct {const char *def;} CfgMeta;
const char *cfg_get(const char *name){(void)name;return "80";}
const CfgMeta *cfg_meta(const char *name){(void)name;static CfgMeta m={"1"};return &m;}
void rt_fatal(const char *format,...){(void)format;abort();}
'''+config+'''
double cfg_double(const char *name){return strtod(cfg_value(name),0);}
int cfg_int(const char *name){return atoi(cfg_value(name));}
unsigned cfg_version(void){return 1;}
static struct {unsigned seen;float adj[4];} C={.seen=~0u};
static int touched_gpu;
void *vk_ctx(void){touched_gpu++;return 0;}
int ready(void *ctx){(void)ctx;touched_gpu++;return 1;}
'''+color+'\n'+sharp+'\n'+rcas+'''
int main(void){
assert(!adjusting());assert(C.adj[0]==0&&C.adj[1]==1&&C.adj[2]==1&&C.adj[3]==1);
assert(!vk_fsr_rcas_on()&&!touched_gpu);
assert(!strcmp(cfg_value("AC_HDR"),"0"));assert(!snap_neutral_value("shadow_scale"));  /* a resolution choice since SS-02 */
assert(!strcmp(cfg_value("AC_UPSCALER"),"bilinear"));
assert(!strcmp(cfg_value("AC_AO"),"off"));assert(!strcmp(cfg_value("AC_CONTACT_SHADOWS"),"0"));
assert(!strcmp(cfg_value("AC_PCSS"),"0"));assert(!strcmp(cfg_value("AC_COLOR_PRESET"),"default"));
assert(!strcmp(cfg_value("AC_FPS"),"80"));
return 0;}
''',encoding='utf-8')
            executable=folder/'neutral.exe'
            subprocess.run([compiler,'-O2','-Wall','-Werror','-I',str(ROOT/'newsnap/overlays'),str(fixture),'-o',str(executable)],check=True,capture_output=True)
            subprocess.run([str(executable)],check=True,capture_output=True)
            temporal=(source/'runtime/vk_dlaa.c').read_text()
            body=function(temporal,'static void sharpen(')
            self.assertLess(body.index('return; // Snap'),body.index('if (vk_hdr_wanted()'))

    def test_launcher_defaults_and_saved_native_presets_stay_neutral(self):
        from newsnap import launcher_settings as settings
        for key,value in settings.NEUTRAL_SETTINGS.items():self.assertEqual(settings.DEFAULTS[key],value)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'settings.ini'
            for backend in ('fsr3','fsr4','dlss','auto'):
                settings.save_settings(path,dict(settings.NEUTRAL_SETTINGS,upscaling=backend,upscaling_quality='native'))
                loaded=settings.load_settings(path)
                self.assertEqual(loaded['upscaling_quality'],'native')
                for key,value in settings.NEUTRAL_SETTINGS.items():self.assertEqual(loaded[key],value)
