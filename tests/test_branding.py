"""Native donor logging/config regressions; no game, GPU or physical input."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'toolchain/astral-release/Astral Chain-Setup'


def adapted(relative):
    text = (ROOT / 'third_party/astral' / relative).read_text(encoding='utf-8')
    if not os.environ.get('NEWSNAP_BRANDING_BASELINE'):
        try:
            from newsnap.branding_adapt import edits
        except ModuleNotFoundError:
            return text
        for old, new in edits().get(relative, []):
            if text.count(old) != 1:
                raise AssertionError((relative, old, text.count(old)))
            text = text.replace(old, new, 1)
    return text


def function(text, signature):
    start = text.index(signature)
    return text[start:text.index('\n}', start) + 2]


class BrandingTests(unittest.TestCase):
    def compile(self, root, source):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(SDK/'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native branding regression')
        file = root/'fixture.c'; file.write_text(source, encoding='utf-8')
        executable = root/'fixture.exe'
        result = subprocess.run([compiler, str(file), '-I'+str(ROOT/'third_party/astral/runtime'), '-o', str(executable)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        return executable

    def test_actual_log_rotation_names_and_old_log_preservation(self):
        text = adapted('runtime/main.c')
        fixture = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define PLAT_PATH_MAX 1024
#define LOG_KEEP 5
enum {LOG_EARLY,LOG_FILE,LOG_OFF};
typedef FILE PlatAppend;
static int g_log_state; static PlatAppend *g_log_file;
static char g_log_path[3072],g_log_early[32768],exe_path[3072];
static size_t g_log_early_n; static uint64_t g_log_bytes;
static int plat_stderr_path(char*p,size_t n){return 0;}
static int plat_exe_path(char*p,size_t n){snprintf(p,n,"%s",exe_path);return 1;}
static char *plat_last_sep(const char*p){return strrchr(p,'/');}
static void plat_file_mkdir_p(const char*p){}
static int plat_file_exists(const char*p){FILE*f=fopen(p,"rb");if(!f)return 0;fclose(f);return 1;}
static int plat_file_replace(const char*a,const char*b){remove(b);return !rename(a,b);}
static PlatAppend *plat_append_open(const char*p){return fopen(p,"ab");}
static void plat_append_write(PlatAppend*f,const void*p,size_t n){fwrite(p,1,n,f);}
static void rt_log(const char*p,...){}
''' + function(text, 'static void log_open(int game)') + r'''
int main(int argc,char**argv){
 snprintf(exe_path,sizeof exe_path,"%s/newsnap.exe",argv[1]);
 log_open(1);assert(g_log_state==LOG_FILE);assert(strstr(g_log_path,"/logs/newsnap.log"));
 fclose(g_log_file);return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); logs=root/'logs'; logs.mkdir()
            original={'newsnap.log':b'current',**{'newsnap.%d.log'%i:str(i).encode() for i in range(1,5)},
                      'astralchain.log':b'legacy-current','totk.1.log':b'legacy-rotated'}
            for name,value in original.items():(logs/name).write_bytes(value)
            exe=self.compile(root,fixture)
            result=subprocess.run([str(exe),root.as_posix()],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((logs/'newsnap.log').read_bytes(),b'')
            for i in range(1,5):
                self.assertEqual((logs/('newsnap.%d.log'%i)).read_bytes(),original['newsnap.log' if i==1 else 'newsnap.%d.log'%(i-1)])
            for name in ('astralchain.log','totk.1.log'):
                self.assertEqual((logs/name).read_bytes(),original[name])

    def test_actual_cfg_legacy_fallback_new_precedence_and_save_preserves_settings(self):
        text=adapted('runtime/cfg.c').replace('#include "host.h"','').replace('#include "platform/platform.h"','')
        preamble=r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
typedef int PlatMutex;
#define PLAT_MUTEX_INIT {0}
static char executable_path[1024]; static int block_legacy_reads;
static void plat_mutex_lock(PlatMutex*p){} static void plat_mutex_unlock(PlatMutex*p){}
static int plat_is_wine(void){return 0;}
static void plat_cpu_boost(int m,uint64_t n,char*p,size_t z){if(z)*p=0;}
static void rt_log(const char*f,...){}
static void rt_fatal(const char*f,...){abort();}
static int res_output_grid(const char*s,uint32_t*w,uint32_t*h){return 0;}
static int plat_file_exists(const char*p){FILE*f=fopen(p,"rb");if(!f)return 0;fclose(f);return 1;}
static int64_t plat_file_size(const char*p){FILE*f=fopen(p,"rb");if(!f)return -1;fseek(f,0,SEEK_END);long n=ftell(f);fclose(f);return n;}
static uint8_t*plat_file_read(const char*p,uint64_t*n){
 if(block_legacy_reads && strstr(p,"astralchain.ini"))return NULL;
 FILE*f=fopen(p,"rb");if(!f)return NULL;fseek(f,0,SEEK_END);*n=ftell(f);rewind(f);
 uint8_t*b=calloc((size_t)*n+1,1);fread(b,1,(size_t)*n,f);fclose(f);
 if(*n>=10 && !memcmp(b,"UNREADABLE",10)){free(b);return NULL;}return b;
}
static int plat_file_write_atomic(const char*p,const void*b,size_t n){FILE*f=fopen(p,"wb");if(!f)return 0;int ok=fwrite(b,1,n,f)==n;fclose(f);return ok;}
static int plat_exe_path(char*p,size_t n){snprintf(p,n,"%s",executable_path);return 1;}
static char*plat_last_sep(const char*p){return strrchr(p,'/');}
'''
        tail=r'''
int main(int argc,char**argv){
 snprintf(executable_path,sizeof executable_path,"%s/newsnap.exe",argv[1]);
 if(!strcmp(argv[2],"bounds") || !strcmp(argv[2],"fits")){
   int fits=!strcmp(argv[2],"fits");
   memset(executable_path,'a',sizeof executable_path);executable_path[fits?1011:1015]='/';executable_path[1023]=0;
   assert(find_ini()==fits);if(fits)assert(strlen(ini_path)==1023);return 0;
 }
 load_ini();
 if(!strcmp(argv[2],"unreadable") || !strcmp(argv[2],"malformed") || !strcmp(argv[2],"empty")){
   assert(!cfg_get("AC_VOLUME"));return 0;
 }
 if(!strcmp(argv[2],"readfailure")){
   assert(cfg_get("AC_VOLUME") && !strcmp(cfg_get("AC_VOLUME"),"25"));
   block_legacy_reads=1;cfg_set("AC_MOTION","0");assert(!cfg_save());assert(!cfg_last_save_ok());return 0;
 }
 assert(cfg_get("AC_VOLUME") && !strcmp(cfg_get("AC_VOLUME"),argv[2]));
 cfg_set("AC_MOTION","0");assert(cfg_save());return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);exe=self.compile(root,preamble+text+tail)
            for case in ('legacy','preferred','unreadable','malformed','empty','readfailure','bounds','fits'):
                with self.subTest(case=case):
                    directory=root/case;directory.mkdir()
                    legacy=directory/'astralchain.ini';legacy.write_bytes(b'; untouched comment\r\nvolume = 25\r\ncustom_option = kept\r\n')
                    old=legacy.read_bytes();new=directory/'newsnap.ini'
                    if case=='preferred':new.write_bytes(b'; preferred\nvolume = 99\n')
                    if case=='unreadable':new.write_bytes(b'UNREADABLE config')
                    if case=='malformed':new.write_bytes(b'not a setting\n')
                    if case=='empty':new.write_bytes(b'')
                    mode={'legacy':'25','preferred':'99'}.get(case,case)
                    result=subprocess.run([str(exe),directory.as_posix(),mode],capture_output=True)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(legacy.read_bytes(),old)
                    if case=='legacy':
                        self.assertTrue(new.is_file())
                        content=new.read_bytes()
                        self.assertIn(b'; untouched comment\r\n',content)
                        self.assertIn(b'volume = 25\r\n',content)
                        self.assertIn(b'custom_option = kept\r\n',content)
                        self.assertIn(b'motion = 0',content)
                    if case=='unreadable':self.assertEqual(new.read_bytes(),b'UNREADABLE config')
                    if case=='preferred':
                        self.assertIn(b'; preferred\nvolume = 99\n',new.read_bytes())
                        self.assertNotIn(b'custom_option',new.read_bytes())
                    if case=='malformed':self.assertEqual(new.read_bytes(),b'not a setting\n')
                    if case=='empty':self.assertEqual(new.read_bytes(),b'')
                    if case=='readfailure':self.assertFalse(new.exists())

    def test_visible_diagnostics_use_product_name(self):
        for file,old in (('runtime/main.c','astralchain+'),('runtime/vk_dlaa.c','next to astralchain.exe?')):
            with self.subTest(file=file):
                self.assertFalse(old in adapted(file),file+': '+old)

    def test_all_anchors_match_pinned_donor_once_and_keep_attribution(self):
        from newsnap.branding_adapt import edits
        for relative in edits():
            with self.subTest(relative=relative):
                original=(ROOT/'third_party/astral'/relative).read_text(encoding='utf-8')
                result=adapted(relative)
                self.assertNotEqual(original,result)
                for line in original.splitlines():
                    if 'Copyright' in line or 'MIT' in line:
                        self.assertIn(line,result)
                for line in result.splitlines():
                    if line.lstrip().startswith('//') or '"' not in line:
                        continue
                    self.assertFalse('astralchain.exe' in line or 'totk.exe' in line,line)
