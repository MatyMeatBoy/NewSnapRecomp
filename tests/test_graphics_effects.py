"""CPU-only regression of the donor's actual prepare_draw preflight control flow."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.graphics_effects_adapt import edits

ROOT = Path(__file__).resolve().parents[1]
PREAMBLE = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "vk_exec.h"
#define NVN_STAGE_VS 0
#define NVN_STAGE_FS 1
#define ONESHOT_WAIT_MS 30000u
#define W_PROGRAM 1
#define W_NO_VS 2
#define W_PIPELINE 3
GfxStats gfx_counters;
typedef struct { int dummy; } MemoKey;
static struct {int valid,has_fs; MemoKey k;const GfxShader *vs,*fs;} SM;
static struct {int valid;VkPipeState s;const VkPipeInfo *info;} PM;
struct GfxShader { GfxShaderRes res; int written, image; };
static struct GfxShader vertex,fragment;
static int recent=1, shader_pending=0, async_calls=0, awaits=0, reflection_queries=0;
static uint32_t last_wait;
static int pending_rounds, pipeline_failure;
static int pending_stage=NVN_STAGE_FS, translation_failure;
static VkPipeInfo pipeline_info;
static int shader_memo_on(void){return 0;}
static int pipe_memo_on(void){return 0;}
static int memo_match(const VkExec*a,uint32_t b,MemoKey*c){return 0;}
static void memo_key(const VkExec*a,uint32_t b,MemoKey*c){}
static void cb_res(VkExec*x){}
static void dummies_init(void){}
static int drop_draw(VkExec*x,int a,const char*b){return 0;}
static void warn_once(int a,const char*b){}
void rt_fatal(const char*a,...) {abort();}
void rt_log(const char*a,...){}
static const char*cfg_get(const char*a){return NULL;}
static int pipe_skip_mode(void){return 2;}
static int skip_shader(const GfxShader*a,const GfxShader*b){return 0;}
static int vk_dlaa_skip_draw(VkExec*a,const GfxShader*b){return 0;}
static uint32_t feedback_prepare(VkExec*a,const GfxShader*b){return 0;}
uint64_t kern_now_ns(void){return 1;}
void perf_count(int a){}
const GfxShader *shader_for(VkExec*a,int st,int*present,int*pending,int await){
 *present=1;if(pending)*pending=shader_pending && st==pending_stage;
 if(await)awaits++;
 if(shader_pending && st==pending_stage && (!await || translation_failure))return NULL;
 return st==NVN_STAGE_FS?&fragment:&vertex;
}
int gfx_shader_resources(const GfxShader*s,int kind,const GfxShaderRes**res){
 reflection_queries++;*res=&s->res;return (kind==GFX_RES_SSBO && s->written) || (kind==GFX_RES_IMG && s->image);
}
void vk_exec_pass_begin(VkExec*x){x->in_pass=1;}
void vk_exec_pass_end(VkExec*x){x->in_pass=0;}
void vk_exec_noatt_dims(const VkExec*x,uint32_t*w,uint32_t*h){*w=128;*h=96;}
VkRect2D vk_exec_scissor(const VkExec*x){return(VkRect2D){{0,0},{128,96}};}
int vk_exec_targets_recent(VkExec*x,int any){return recent;}
void vk_exec_targets_describe(VkExec*x,char*s,size_t n){if(n)*s=0;}
uint32_t vk_texture_slots_gen(void){return 0;}
int nvn_depth_minus_w(void){return 0;}
VkPipeline vk_pipeline_graphics_async(const VkPipeState*s,const VkPipeInfo**info,int*pending,uint32_t wait){
 async_calls++;last_wait=wait;
 if(pipeline_failure){*pending=0;*info=NULL;return VK_NULL_HANDLE;}
 *pending=!wait || pending_rounds-->0;*info=*pending?NULL:&pipeline_info;
 return *pending?VK_NULL_HANDLE:(VkPipeline)(uintptr_t)1;
}
'''
MAIN = r'''
static void reset(void){
 recent=1;shader_pending=0;async_calls=awaits=reflection_queries=0;
 pending_rounds=0;pipeline_failure=0;last_wait=0;
 pending_stage=NVN_STAGE_FS;translation_failure=0;
 vertex=(struct GfxShader){0};fragment=(struct GfxShader){0};SM.valid=PM.valid=0;
}
int main(void){
 VkExec ex={0};prog_t prog={0};ex.prog=&prog;ex.pass_w=128;ex.pass_h=96;
 reset();fragment.written=1;fragment.res.flags=1;fragment.res.slot=0;fragment.res.handle=328;
 if(!prepare_draw(&ex,3,3,0)||!last_wait||!reflection_queries)return 1;
 reset();vertex.written=1;vertex.res.flags=1;
 if(!prepare_draw(&ex,3,48,0)||!last_wait)return 2;
 reset();fragment.image=1;fragment.res.flags=4;
 if(!prepare_draw(&ex,3,48,0)||!last_wait)return 3;
 reset();fragment.written=1;fragment.res.flags=0;
 if(prepare_draw(&ex,3,3,0)||last_wait)return 4;
 reset();fragment.image=1;fragment.res.flags=8;
 if(prepare_draw(&ex,3,3,0)||last_wait)return 5;
 reset();shader_pending=1;fragment.written=1;fragment.res.flags=1;
 if(!prepare_draw(&ex,3,3,0)||awaits!=1)return 6;
 reset();shader_pending=1;
 if(prepare_draw(&ex,3,3,0)||awaits!=1||last_wait)return 7;
 reset();fragment.written=1;fragment.res.flags=1;pending_rounds=2;
 if(!prepare_draw(&ex,3,3,0)||async_calls<3)return 8;
 reset();fragment.written=1;fragment.res.flags=1;pipeline_failure=1;
 if(prepare_draw(&ex,3,3,0)||async_calls!=1)return 9;
 reset();shader_pending=1;pending_stage=NVN_STAGE_VS;vertex.written=1;vertex.res.flags=1;
 if(!prepare_draw(&ex,3,3,0)||awaits!=1)return 10;
 reset();shader_pending=1;translation_failure=1;
 if(prepare_draw(&ex,3,3,0)||awaits!=1||async_calls)return 11;
 puts("PASS: VS/PS SSBO and image stores complete; pure pipelines still skip; unknown reflection awaited; repeated pending and actual failure separated");
 return 0;
}
'''

class GraphicsEffectsTests(unittest.TestCase):
    def test_actual_prepare_draw_preserves_storage_side_effects(self):
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not (sdk / 'runtime/deps/include/vulkan/vulkan.h').is_file() or not (Path(compiler).is_file() or shutil.which(compiler)):
            self.skipTest('clang and bundled Vulkan headers required')
        source = (ROOT / 'third_party/astral/runtime/vk_exec_draw.c').read_text(encoding='utf-8')
        patches = edits()['runtime/vk_exec_draw.c']
        for old, new in patches:
            self.assertEqual(source.count(old), 1, old[:100])
            source = source.replace(old, new, 1)
        start = source.index('static int prepare_draw(')
        stop = source.index('    bind_pipeline(ex,', start)
        # Keep the actual donor preflight through pending/failure returns; Vulkan
        # command recording after this boundary is deliberately outside CPU scope.
        preflight = source[start:stop] + '    return 1;\n}\n'
        support = ''
        if 'static int snap_shader_writes(' in source:
            support = source[source.index('static int snap_shader_writes('):source.index('// Pass, shaders, pipeline, fixed state and resources for a draw.')]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            c = folder / 'effects.c'
            exe = folder / ('effects.exe' if os.name == 'nt' else 'effects')
            c.write_text(PREAMBLE + support + preflight + MAIN, encoding='utf-8')
            compile_result = subprocess.run([compiler, '-std=c11', '-I'+str(ROOT/'third_party/astral/runtime'),
                '-I'+str(sdk/'runtime/deps/include'), '-I'+str(sdk/'runtime/deps/include/vma'), str(c), '-o', str(exe)], capture_output=True, timeout=60)
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr.decode(errors='replace'))
            result = subprocess.run([str(exe)], capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, 'actual prepare_draw preflight case '+str(result.returncode)+' failed: '+result.stderr.decode(errors='replace'))
