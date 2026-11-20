import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT, UPSTREAM


class ShaderCacheIoTests(unittest.TestCase):
    def test_all_persistence_boundaries_drain_only_shader_metadata(self):
        from newsnap.shader_cache_io_adapt import edits
        text=(UPSTREAM/'runtime/gfx_shader.c').read_text(encoding='utf-8')
        for before,after in edits()['runtime/gfx_shader.c']:
            self.assertEqual(text.count(before),1,before)
            text=text.replace(before,after,1)
        self.assertEqual(text.count('snap_shader_cache_write(p,'),2)
        self.assertEqual(text.count('snap_shader_cache_flush();'),5)
        self.assertIn('plat_file_flush(spv_path), plat_file_flush(res_path)',text)
        self.assertIn('void gfx_shader_drop_memory(void) {\n    snap_shader_cache_flush();',text)
        self.assertLess(text.index('snap_shader_cache_flush(); // standalone'),text.index("RecHeader h = {{'A', 'C', 'S', 'P', 'R', 'P'}"))

    def test_bounded_owned_snapshots_and_concurrent_drain(self):
        header = ROOT / 'newsnap/overlays/snap_shader_cache_io.h'
        self.assertTrue(header.is_file(), 'deferred shader metadata writer is missing')
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if os.name != 'nt' or not cc:
            self.skipTest('Windows native compiler fixture')
        source = r'''
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "platform/platform.h"
static int writes, bad, last[4], small_writes;
static volatile LONG done;
static void *test_alloc(size_t n);
#define malloc test_alloc
#include "snap_shader_cache_io.h"
#undef malloc
static int fail_alloc;
static void *test_alloc(size_t n) { return fail_alloc ? NULL : malloc(n); }
void plat_mutex_lock(PlatMutex *m) { AcquireSRWLockExclusive((SRWLOCK*)m); }
void plat_mutex_unlock(PlatMutex *m) { ReleaseSRWLockExclusive((SRWLOCK*)m); }
int plat_file_write_atomic(const char *path, const void *data, size_t n) {
    writes++;
    if (n==sizeof(int)*2) {
        const int *v=data;
        if (v[0]<0 || v[0]>3 || v[1]!=++last[v[0]]) bad=1;
    } else if (n==4) {
        if (strcmp(path,"cache/original.use") || memcmp(data,"snap",4)) bad=2;
        small_writes++;
    }
    return 1;
}
static DWORD WINAPI producer(void *arg) {
    int id=(int)(intptr_t)arg;
    for(int i=1;i<=1000;i++) { int v[2]={id,i}; snap_shader_cache_write("cache/input.in",v,sizeof v); }
    return 0;
}
static DWORD WINAPI drain(void *arg) {
    (void)arg;
    while(!InterlockedCompareExchange(&done,0,0)) { snap_shader_cache_flush(); Sleep(0); }
    snap_shader_cache_flush(); return 0;
}
int main(void) {
    char path[64]="cache/original.use", data[5]="snap";
    snap_shader_cache_write(path,data,4);
    memset(path,'x',strlen(path));memset(data,'x',4);
    if(writes) return 1;
    snap_shader_cache_flush();
    if(writes!=1 || small_writes!=1 || bad) return 2;
    fail_alloc=1;snap_shader_cache_write("cache/original.use","snap",4);fail_alloc=0;
    if(writes!=2) return 3;
    void *large=calloc(1,9u*1024*1024);
    snap_shader_cache_write("cache/large.in",large,9u*1024*1024);free(large);
    if(writes!=3) return 4;
    large=calloc(1,2u*1024*1024);
    for(int i=0;i<5;i++) {
        snap_shader_cache_write("cache/pressure.in",large,2u*1024*1024);
        if(snap_shader_bytes>SNAP_SHADER_CACHE_LIMIT) return 8;
    }
    free(large);snap_shader_cache_flush();
    if(writes!=8) return 9;
    HANDLE worker=CreateThread(NULL,0,drain,NULL,0,NULL), p[4];
    for(int i=0;i<4;i++)p[i]=CreateThread(NULL,0,producer,(void*)(intptr_t)i,0,NULL);
    WaitForMultipleObjects(4,p,TRUE,INFINITE);
    InterlockedExchange(&done,1);WaitForSingleObject(worker,INFINITE);
    for(int i=0;i<4;i++) { CloseHandle(p[i]); if(last[i]!=1000) return 5; }
    CloseHandle(worker);
    if(writes!=4008 || bad) return 6;
    snap_shader_cache_flush();
    return writes==4008 ? 0 : 7;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder); test=folder/'test.c';test.write_text(source)
            exe=folder/'test.exe'
            result=subprocess.run([cc,str(test),'-std=c11','-I',str(header.parent),'-I',str(UPSTREAM/'runtime'),
                                   '-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':
    unittest.main()
