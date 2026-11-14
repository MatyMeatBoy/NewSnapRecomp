"""CPU fixtures for opt-in presentation observations; never start Vulkan or a window."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SDK=ROOT/'toolchain/astral-release/Astral Chain-Setup'


def adapted():
    source=(ROOT/'third_party/astral/runtime/gfx_present.c').read_text(encoding='utf-8')
    try:
        from newsnap.present_trace_adapt import edits
    except ModuleNotFoundError:
        return source
    for old,new in edits()['runtime/gfx_present.c']:
        if source.count(old)!=1:raise AssertionError((old,source.count(old)))
        source=source.replace(old,new,1)
    return source


def function(text, signature):
    start=text.index(signature)
    return text[start:text.index('\n}',start)+2]


class PresentTraceTests(unittest.TestCase):
    def compile(self,root,source):
        cc=os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(SDK/'llvm/bin/clang.exe')
        if not Path(cc).is_file() and not shutil.which(cc):self.skipTest('clang required')
        (root/'fixture.c').write_text(source,encoding='utf-8')
        overlays=ROOT/'newsnap/overlays'
        header=overlays/'snap_present_trace.h';implementation=overlays/'snap_present_trace.c'
        if header.exists():
            (root/header.name).write_bytes(header.read_bytes())
            (root/implementation.name).write_bytes(implementation.read_bytes())
        else:
            (root/'snap_present_trace.h').write_text('''#include <stdint.h>
enum { SNAP_PRESENT_ACQUIRE, SNAP_PRESENT_FENCE, SNAP_PRESENT_QUEUE, SNAP_PRESENT_REBUILD };
extern int snap_present_trace_on;
uint64_t snap_present_trace_begin(void);
void snap_present_trace_end(int,uint64_t,int);
void snap_present_trace_modes(const char*,const char*,uint32_t,const uint32_t*,uint32_t,int);
void snap_present_trace_swapchain(uint32_t,uint32_t,uint32_t,uint32_t,int);
''')
            (root/'snap_present_trace.c').write_text('''#include "snap_present_trace.h"
int snap_present_trace_on;
uint64_t snap_present_trace_begin(void){return 0;}
void snap_present_trace_end(int a,uint64_t b,int c){}
void snap_present_trace_modes(const char*a,const char*b,uint32_t c,const uint32_t*d,uint32_t e,int f){}
void snap_present_trace_swapchain(uint32_t a,uint32_t b,uint32_t c,uint32_t d,int e){}
''')
        (root/'host.h').write_text('void rt_log(const char*,...);\n')
        (root/'platform').mkdir()
        (root/'platform/platform.h').write_text('#include <stdint.h>\nuint64_t plat_now_ns(void);\n')
        exe=root/'fixture.exe'
        result=subprocess.run([cc,str(root/'fixture.c'),str(root/'snap_present_trace.c'),'-I'+str(root),'-o',str(exe)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return exe

    def test_native_off_on_bounds_aggregation_and_results(self):
        fixture=r'''
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snap_present_trace.h"
static uint64_t now=10;static unsigned clocks,lines;static char output[32768];
uint64_t plat_now_ns(void){clocks++;return now;}
void rt_log(const char*f,...){size_t n=strlen(output);va_list ap;va_start(ap,f);vsnprintf(output+n,sizeof output-n,f,ap);va_end(ap);strcat(output,"\n");lines++;}
int main(int argc,char**argv){
 int enabled=!strcmp(argv[1],"on");assert(!!snap_present_trace_on==enabled);
 uint32_t modes[]={0,2};
 if(!enabled){
   for(int i=0;i<1000;i++){uint64_t t=snap_present_trace_begin();snap_present_trace_end(SNAP_PRESENT_ACQUIRE,t,2);}
   snap_present_trace_modes("mailbox","fifo",2,modes,2,0);snap_present_trace_swapchain(3,3,1920,1080,0);
   assert(!clocks && !lines);return 0;
 }
 uint64_t t=snap_present_trace_begin();now+=100;snap_present_trace_end(SNAP_PRESENT_ACQUIRE,t,0);
 assert(lines==1);assert(strstr(output,"operation=acquire"));assert(strstr(output,"count=1"));assert(strstr(output,"sum_ns=100"));
 for(int i=1;i<120;i++){
   if(i==119)now=2000000000ull;
   t=snap_present_trace_begin();now+=i==1?20:100;snap_present_trace_end(SNAP_PRESENT_ACQUIRE,t,i==1?2:0);
 }
 assert(lines==2);assert(strstr(output,"count=120"));assert(strstr(output,"sum_ns=11920"));
 assert(strstr(output,"min_ns=20"));assert(strstr(output,"max_ns=100"));assert(strstr(output,"other_results=1"));
 t=snap_present_trace_begin();now+=500;snap_present_trace_end(SNAP_PRESENT_QUEUE,t,-1000001004);
 assert(strstr(output,"last_result=-1000001004"));
 t=snap_present_trace_begin();now+=1000;snap_present_trace_end(SNAP_PRESENT_REBUILD,t,1);
 assert(strstr(output,"operation=rebuild"));
 snap_present_trace_modes("mailbox","fifo",2,modes,2,0);snap_present_trace_swapchain(3,4,1920,1080,0);
 assert(strstr(output,"requested=mailbox effective=fifo"));assert(strstr(output,"enumerated=0,2"));
 assert(strstr(output,"images_requested=3 images_actual=4"));
 unsigned before=lines;
 for(int i=0;i<1000;i++)snap_present_trace_swapchain(3,4,1920,1080,0);
 assert(lines==before);return 0;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            exe=self.compile(Path(temporary),fixture)
            for value,expected in ((None,'off'),('0','off'),('true','off'),('1','on')):
                with self.subTest(value=value):
                    env=dict(os.environ);env.pop('AC_SNAP_PRESENT_TRACE',None)
                    if value is not None:env['AC_SNAP_PRESENT_TRACE']=value
                    result=subprocess.run([str(exe),expected],env=env,capture_output=True)
                    self.assertEqual(result.returncode,0,result.stderr)

    def test_real_call_seams_keep_retries_and_results(self):
        original=(ROOT/'third_party/astral/runtime/gfx_present.c').read_text(encoding='utf-8')
        source=adapted()
        self.assertEqual(source.count('snap_present_trace_end(SNAP_PRESENT_ACQUIRE,'),2)
        self.assertEqual(source.count('snap_present_trace_end(SNAP_PRESENT_FENCE,'),2)
        self.assertEqual(source.count('snap_present_trace_end_at(SNAP_PRESENT_QUEUE,'),1)
        self.assertEqual(source.count('snap_present_trace_end(SNAP_PRESENT_REBUILD,'),1)
        for call in ('vkAcquireNextImageKHR(','vkWaitForFences(','vkQueuePresentKHR(','vkCreateSwapchainKHR('):
            self.assertEqual(source.count(call),original.count(call),call)
        self.assertIn('if (snap_fence_result != VK_SUCCESS)',source)
        self.assertIn('if (r != VK_SUCCESS && r != VK_SUBOPTIMAL_KHR) goto out;',source)
        self.assertIn('return snap_rebuild_result;',source)

    def test_actual_mode_selection_flip_and_rebuild_keep_policy(self):
        source=adapted()
        if 'static int snap_create_swapchain_impl(' not in source:
            self.fail('missing opt-in wrapper')
        fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snap_present_trace.h"
typedef int VkResult;typedef int VkPhysicalDevice;typedef int VkPresentModeKHR;
#define VK_SUCCESS 0
#define VK_INCOMPLETE 5
#define VK_SUBOPTIMAL_KHR 1000001003
#define VK_ERROR_OUT_OF_DATE_KHR -1000001004
#define VK_PRESENT_MODE_FIFO_KHR 2
#define VK_PRESENT_MODE_MAILBOX_KHR 1
#define VK_PRESENT_MODE_IMMEDIATE_KHR 0
#define VK_STRUCTURE_TYPE_PRESENT_INFO_KHR 1
typedef struct {int gfx_queue;} VkCtx;
typedef struct {int sType;unsigned waitSemaphoreCount;int*pWaitSemaphores;unsigned swapchainCount;int*pSwapchains;unsigned*pImageIndices;} VkPresentInfoKHR;
static VkCtx context;
static int g_surface,g_sc=1,g_flip_on,g_dirty,g_render_done[4],queue_calls,query_calls,lock_depth;
static unsigned g_flip_idx,clocks;static uint64_t now;
static const char*g_present_got="";static int response,last_reported,rebuild_result;
static char output[16384];
uint64_t plat_now_ns(void){clocks++;return now;}
void rt_log(const char*f,...){size_t n=strlen(output);va_list ap;va_start(ap,f);vsnprintf(output+n,sizeof output-n,f,ap);va_end(ap);strcat(output,"\n");}
static const char*cfg_value(const char*p){return "mailbox";}
static VkCtx*vk_ctx(void){return &context;}
static int vkGetPhysicalDeviceSurfacePresentModesKHR(int a,int b,uint32_t*n,int*m){
 query_calls++;if(m){assert(*n>=2);m[0]=2;m[1]=3;}*n=2;return 0;
}
static void vk_queue_lock(void){assert(!lock_depth);lock_depth++;}
static void vk_queue_unlock(void){assert(lock_depth==1);lock_depth--;now+=1000;}
static int vkQueuePresentKHR(int q,const VkPresentInfoKHR*p){assert(lock_depth==1);queue_calls++;now+=500;return response;}
static void vk_device_fault_report(int r){last_reported=r;}
static int plat_xchg32(int*p,int n){int old=*p;*p=n;return old;}
static int snap_create_swapchain_impl(void){now+=700;return rebuild_result;}
''' + function(source,'static VkPresentModeKHR pick_present_mode(') + '\n' + function(source,'static void flip_locked(') + '\n' + function(source,'static int create_swapchain(void)') + r'''
int main(void){
 assert(pick_present_mode(1)==VK_PRESENT_MODE_FIFO_KHR);assert(query_calls==2);assert(!strcmp(g_present_got,"fifo"));
 flip_locked();assert(!queue_calls);
 g_flip_on=1;g_sc=0;flip_locked();assert(!queue_calls && !g_flip_on);g_sc=1;
 int results[]={VK_ERROR_OUT_OF_DATE_KHR,VK_SUCCESS,VK_SUBOPTIMAL_KHR};
 for(int i=0;i<3;i++){
   g_dirty=0;g_flip_on=1;response=results[i];flip_locked();
   assert(!g_flip_on && !lock_depth);assert(last_reported==response);assert(g_dirty==(i!=1));
 }
 assert(queue_calls==3);
 rebuild_result=0;assert(create_swapchain()==0);rebuild_result=1;assert(create_swapchain()==1);
 if(snap_present_trace_on){
   assert(strstr(output,"operation=queue_present count=1 sum_ns=500"));
   assert(strstr(output,"operation=rebuild count=1 sum_ns=700"));
 }else assert(!clocks);
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            exe=self.compile(Path(temporary),fixture)
            for enabled in ('0','1'):
                env={**os.environ,'AC_SNAP_PRESENT_TRACE':enabled}
                result=subprocess.run([str(exe)],env=env,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
