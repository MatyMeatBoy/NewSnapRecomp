"""Exercise the actual native status adapter with a mocked Vulkan timing query."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT
from newsnap.vrr_adapt import edits


class VrrTests(unittest.TestCase):
    def test_exact_seams_and_optional_negotiation(self):
        for name, changes in edits().items():
            text=(ROOT/'third_party/astral'/name).read_text(encoding='utf-8')
            for before,after in changes:
                self.assertEqual(text.count(before),1,(name,before))
                text=text.replace(before,after)
            if name.endswith('vk_device.c'):
                self.assertLess(text.index('CHAIN(snap_present_timing,'),text.index('CHAIN(gpl,'))
                self.assertIn('presentAtAbsoluteTime = VK_FALSE',text)
                self.assertIn('presentAtRelativeTime = VK_FALSE',text)
            self.assertNotIn('VK_SWAPCHAIN_CREATE_PRESENT_TIMING_BIT_EXT',text)
            self.assertNotIn('vkSetSwapchainPresentTimingQueueSizeEXT(',text)

    def test_native_query_classification_invalidation_and_failure(self):
        kit=ROOT/'toolchain/astral-release/Astral Chain-Setup'
        compiler=kit/'llvm/bin/clang.exe'
        if not compiler.is_file():self.skipTest('pinned LLVM toolchain unavailable')
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);fixture=folder/'vrr.c';exe=folder/'vrr.exe'
            fixture.write_text(r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "snap_vrr.h"
#include "snap_vrr_writer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint64_t now=1,duration,interval;
static VkResult response;
static unsigned queries,writes;
static char published[2048];
uint64_t plat_now_ns(void){return now;}
uint32_t plat_process_id(void){return 42;}
size_t plat_getenv(const char *name,char *out,size_t capacity){assert(!strcmp(name,"NEWSNAP_DISPLAY_STATUS"));snprintf(out,capacity,"C:/private/status.json");return 1;}
int plat_file_write_atomic(const char *path,const void *data,size_t size){assert(!strcmp(path,"C:/private/status.json"));assert(size<sizeof published);memcpy(published,data,size);published[size]=0;writes++;return 1;}
void snap_vrr_writer_start(void){}
void snap_vrr_writer_stop(void){}
void snap_vrr_writer_publish(const SnapVrrStatus *status){SnapVrrStatus copy=*status;copy.process_id=42;assert(snap_vrr_json(&copy,published,sizeof published));writes++;}
HWND gfx_window_handle(void){return NULL;}
static VKAPI_ATTR VkResult VKAPI_CALL query(VkDevice device,VkSwapchainKHR swapchain,VkSwapchainTimingPropertiesEXT *timing,uint64_t *counter){
    assert(device==(VkDevice)1 && swapchain);assert(timing->sType==VK_STRUCTURE_TYPE_SWAPCHAIN_TIMING_PROPERTIES_EXT);
    queries++;timing->refreshDuration=duration;timing->refreshInterval=interval;*counter=queries;return response;
}
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vkGetDeviceProcAddr(VkDevice device,const char *name){assert(device==(VkDevice)1);assert(!strcmp(name,"vkGetSwapchainTimingPropertiesEXT"));return (PFN_vkVoidFunction)query;}
int main(void){
    SnapVrrStatus s;char json[2048],tiny[8];
    snap_vrr_reset(&s,5,1,"initial");s.timing_api_available=1;
    snap_vrr_apply_result(&s,VK_SUCCESS,100,UINT64_MAX,2);assert(s.presentation==SNAP_REFRESH_VARIABLE);
    snap_vrr_apply_result(&s,VK_NOT_READY,100,UINT64_MAX,3);assert(s.presentation==SNAP_REFRESH_UNKNOWN && !s.refresh_duration_ns);
    snap_vrr_apply_result(&s,VK_SUCCESS,100,100,4);assert(s.presentation==SNAP_REFRESH_FIXED);
    snap_vrr_apply_result(&s,VK_SUCCESS,0,UINT64_MAX,5);assert(s.presentation==SNAP_REFRESH_UNKNOWN);
    snap_vrr_apply_result(&s,VK_SUCCESS,100,0,6);assert(s.presentation==SNAP_REFRESH_UNKNOWN);
    snap_vrr_apply_result(&s,VK_SUCCESS,100,20,7);assert(s.presentation==SNAP_REFRESH_UNKNOWN);
    snap_vrr_apply_result(&s,VK_ERROR_SURFACE_LOST_KHR,100,UINT64_MAX,8);assert(s.presentation==SNAP_REFRESH_UNKNOWN);
    assert(snap_vrr_json(&s,json,sizeof json));assert(strstr(json,"\"source\":\"none\""));
    assert(!snap_vrr_json(&s,tiny,sizeof tiny) && !tiny[0]);
    strcpy(s.monitor_name,"name\"\\\n");assert(snap_vrr_json(&s,json,sizeof json));assert(strstr(json,"name\\\"\\\\\\u000a"));
    snap_vrr_reset(&s,6,9,"monitor_changed");assert(s.generation==6 && s.presentation==SNAP_REFRESH_UNKNOWN);
    const char *extensions[5]={"VK_KHR_swapchain"};uint32_t n=1;
    assert(snap_vrr_append_extension(extensions,&n,5,"VK_KHR_swapchain") && n==1);
    assert(snap_vrr_append_extension(extensions,&n,5,"VK_EXT_present_timing") && n==2);
    assert(!snap_vrr_append_extension(extensions,&n,2,"extra") && n==2);
    VkExtensionProperties p[4]={0};
    const char *names[]={"VK_EXT_present_timing","VK_KHR_present_id2","VK_KHR_calibrated_timestamps","VK_KHR_swapchain"};
    for(unsigned i=0;i<4;i++)snprintf(p[i].extensionName,sizeof p[i].extensionName,"%s",names[i]);
    snap_vrr_instance_capabilities=0;assert(!snap_vrr_extension_bundle(p,4));
    snap_vrr_instance_capabilities=1;assert(!snap_vrr_extension_bundle(p,3));assert(snap_vrr_extension_bundle(p,4));
    snap_vrr_device_ready((VkDevice)1,0);snap_vrr_swapchain_changed((VkSwapchainKHR)2,"fifo");
    snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)2,VK_SUCCESS);assert(!queries);
    assert(strstr(published,"extension_unavailable") && strstr(published,"\"presentation\":\"unknown\""));
    snap_vrr_device_ready((VkDevice)1,1);snap_vrr_swapchain_changed((VkSwapchainKHR)2,"mailbox");
    response=VK_NOT_READY;snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)2,VK_SUCCESS);assert(queries==1);
    response=VK_SUCCESS;duration=16666667;interval=duration;now+=1000000000ull;
    snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)2,VK_SUCCESS);assert(queries==2 && strstr(published,"\"presentation\":\"fixed\""));
    unsigned previous_writes=writes;snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)2,VK_SUCCESS);assert(queries==2 && writes==previous_writes);
    snap_vrr_swapchain_changed((VkSwapchainKHR)3,"immediate");assert(strstr(published,"\"presentation\":\"unknown\""));
    interval=UINT64_MAX;snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)3,VK_SUCCESS);assert(queries==3 && strstr(published,"\"presentation\":\"variable\""));
    snap_vrr_after_present((VkDevice)1,(VkSwapchainKHR)3,VK_ERROR_OUT_OF_DATE_KHR);assert(strstr(published,"\"source\":\"none\""));
    snap_vrr_shutdown();assert(strstr(published,"stopped") && strstr(published,"\"presentation\":\"unknown\""));
    puts(published);return 0;
}
''',encoding='utf-8')
            sources=ROOT/'newsnap/overlays'
            subprocess.run([str(compiler),'-O2','-Wall','-Werror','-I',str(sources),'-I',str(ROOT/'third_party/astral/runtime'),
                '-I',str(kit/'runtime/deps/include'),str(fixture),str(sources/'snap_vrr.c'),str(sources/'snap_vrr_core.c'),
                '-luser32','-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            status=json.loads(result.stdout)
            self.assertEqual(status['format'],'newsnap-display-status-v1')
            self.assertEqual(status['driver_enabled'],'unknown')
            self.assertEqual(status['display_support'],'unknown')
            self.assertEqual(status['source'],'none')
            self.assertEqual(status['actual_present_mode'],'immediate')
            self.assertEqual(status['process_id'],42)

    def test_native_latest_only_writer_never_waits_for_io(self):
        kit=ROOT/'toolchain/astral-release/Astral Chain-Setup';compiler=kit/'llvm/bin/clang.exe'
        if not compiler.is_file():self.skipTest('pinned LLVM toolchain unavailable')
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);fixture=folder/'writer.c';exe=folder/'writer.exe'
            fixture.write_text(r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "snap_vrr_writer.h"
#include "platform/platform.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
struct PlatThread {HANDLE handle;PlatThreadFn fn;void *arg;};
static DWORD WINAPI run(void *value){PlatThread *t=value;t->fn(t->arg);return 0;}
PlatThread *plat_thread_new(PlatThreadFn fn,void *arg,const char *name){(void)name;PlatThread *t=calloc(1,sizeof *t);assert(t);t->fn=fn;t->arg=arg;t->handle=CreateThread(NULL,0,run,t,0,NULL);assert(t->handle);return t;}
void plat_thread_join(PlatThread *t){assert(WaitForSingleObject(t->handle,10000)==WAIT_OBJECT_0);CloseHandle(t->handle);free(t);}
void plat_mutex_lock(PlatMutex *m){AcquireSRWLockExclusive((SRWLOCK *)m);}
void plat_mutex_unlock(PlatMutex *m){ReleaseSRWLockExclusive((SRWLOCK *)m);}
void plat_cond_wait(PlatCond *c,PlatMutex *m){assert(SleepConditionVariableSRW((CONDITION_VARIABLE *)c,(SRWLOCK *)m,10000,0));}
void plat_cond_signal(PlatCond *c){WakeConditionVariable((CONDITION_VARIABLE *)c);}
uint32_t plat_process_id(void){return 42;}
static int absent;
size_t plat_getenv(const char *name,char *out,size_t cap){(void)name;if(absent)return 0;snprintf(out,cap,"C:/private/status.json");return 1;}
static HANDLE entered,release_io;
static LONG writes,logs,fail;
static char published[2048];
void rt_log(const char *format,...){(void)format;InterlockedIncrement(&logs);}
int plat_file_write_atomic(const char *path,const void *data,size_t size){
    assert(!strcmp(path,"C:/private/status.json"));
    LONG call=InterlockedIncrement(&writes);
    if(call==1){SetEvent(entered);assert(WaitForSingleObject(release_io,10000)==WAIT_OBJECT_0);}
    if(InterlockedCompareExchange(&fail,0,0))return 0;
    assert(size<sizeof published);memcpy(published,data,size);published[size]=0;return 1;
}
int main(void){
    entered=CreateEventW(NULL,TRUE,FALSE,NULL);release_io=CreateEventW(NULL,TRUE,FALSE,NULL);assert(entered&&release_io);
    SnapVrrStatus s;snap_vrr_reset(&s,1,1,"test");s.timing_api_available=1;snap_vrr_apply_result(&s,VK_SUCCESS,100,UINT64_MAX,1);
    snap_vrr_writer_start();snap_vrr_writer_publish(&s);assert(WaitForSingleObject(entered,10000)==WAIT_OBJECT_0);
    for(unsigned i=2;i<=100;i++){s.generation=i;snap_vrr_writer_publish(&s);}
    assert(writes==1);SetEvent(release_io);snap_vrr_writer_stop();assert(writes==2);
    assert(strstr(published,"\"generation\":100"));
    // Failed writes clear queued old observations; the next report explicitly becomes unknown.
    writes=0;fail=1;ResetEvent(entered);snap_vrr_writer_start();snap_vrr_writer_publish(&s);
    assert(WaitForSingleObject(entered,10000)==WAIT_OBJECT_0);
    for(unsigned i=0;i<1000 && !logs;i++)Sleep(1);assert(logs==1);
    fail=0;snap_vrr_writer_publish(&s);snap_vrr_writer_stop();assert(strstr(published,"status_write_failed"));
    assert(strstr(published,"\"presentation\":\"unknown\""));assert(logs==1);
    absent=1;LONG before=writes;snap_vrr_writer_start();snap_vrr_writer_publish(&s);snap_vrr_writer_stop();assert(writes==before);
    CloseHandle(entered);CloseHandle(release_io);puts(published);return 0;
}
''',encoding='utf-8')
            sources=ROOT/'newsnap/overlays'
            compiled=subprocess.run([str(compiler),'-O2','-Wall','-Werror','-I',str(sources),'-I',str(ROOT/'third_party/astral/runtime'),
                '-I',str(kit/'runtime/deps/include'),str(fixture),str(sources/'snap_vrr_writer.c'),str(sources/'snap_vrr_core.c'),
                '-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=20)
            self.assertEqual(json.loads(result.stdout)['reason'],'status_write_failed')


if __name__=='__main__':unittest.main()
