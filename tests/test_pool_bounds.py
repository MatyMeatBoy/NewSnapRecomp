"""Execute the actual adapted pool-binding function with deterministic Vulkan stubs."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def binding_source():
    source = (ROOT / 'third_party/astral/runtime/vk_texture.c').read_text(encoding='utf-8')
    try:
        from newsnap.pool_bounds_adapt import edits
    except ModuleNotFoundError:
        pass  # Initial red run executes the unchanged donor function.
    else:
        for before, after in edits()['runtime/vk_texture.c']:
            if source.count(before) != 1:
                raise AssertionError('pool binding source seam changed')
            source = source.replace(before, after, 1)
    start = source.index('static int bind_pool_memory(')
    end = source.index('\n}\n', start) + 3
    marker = source.find('// SNAP_POOL_BOUNDS')
    return source[marker if 0 <= marker < start else start:end]


FIXTURE = r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <pthread.h>
#endif
typedef uint64_t VkImage;
typedef struct {uint64_t size,alignment;uint32_t memoryTypeBits;} VkMemoryRequirements;
typedef struct {int device,vma;} VkCtx;
typedef struct {int memoryType;} VmaAllocationInfo;
typedef struct {void *alloc;uint64_t alloc_offset,avail;} VkMemSpan;
typedef struct {struct {uint32_t width,height,format;} d;} Texture;
typedef struct {struct {int depth,stencil,vk;} f;struct {uint64_t addr;} pub;
                Texture t;void *bound_to;} Tex;
#define VK_SUCCESS 0
static VkMemoryRequirements req={128,64,1};
static int queries,resolves,infos,binds,logs,colour_logs,depth_logs,enabled,bind_failure,no_alloc;
static int ordered,stage;
static char last[1024];
static const char *fixture_getenv(const char *name){return enabled?"1":NULL;}
#define getenv fixture_getenv
static void rt_log(const char *fmt,...){
 __atomic_fetch_add(&logs,1,__ATOMIC_RELAXED);
 char message[1024];va_list args;va_start(args,fmt);vsnprintf(message,sizeof message,fmt,args);va_end(args);
 __atomic_fetch_add(strstr(message,"decision=policy_depth")?&depth_logs:&colour_logs,1,__ATOMIC_RELAXED);
 // Concurrent test observes counters only; never share a mutable log buffer.
 if(ordered)strcpy(last,message);
}
static void vkGetImageMemoryRequirements(int d,VkImage image,VkMemoryRequirements *out){
 __atomic_fetch_add(&queries,1,__ATOMIC_RELAXED);*out=req;
 if(ordered && stage++!=0)abort();
}
static int vk_mem_resolve(uint64_t addr,uint64_t size,VkMemSpan *out){
 __atomic_fetch_add(&resolves,1,__ATOMIC_RELAXED);
 if(ordered && stage++!=1)abort();
 if(addr>256 || size>256-addr)return 0;
 *out=(VkMemSpan){no_alloc?NULL:(void *)1,addr,256-addr};return 1;
}
static void vmaGetAllocationInfo(int v,void *a,VmaAllocationInfo *info){
 __atomic_fetch_add(&infos,1,__ATOMIC_RELAXED);info->memoryType=0;
 if(ordered && stage++!=2)abort();
}
static int vmaBindImageMemory2(int v,void *a,uint64_t off,VkImage image,void *next){
 __atomic_fetch_add(&binds,1,__ATOMIC_RELAXED);
 if(ordered && stage++!=3)abort();return bind_failure?-1:0;
}
'''

MAIN = r'''
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s; log=%s\n",__LINE__,#x,last);return 1;}}while(0)
static void reset(void){queries=resolves=infos=binds=stage=0;no_alloc=bind_failure=0;req=(VkMemoryRequirements){128,64,1};}
static Tex texture(uint64_t addr){Tex t={.f.vk=37,.pub.addr=addr,.t.d={1080,720,0x25}};return t;}
#ifdef _WIN32
static DWORD WINAPI worker(void *unused){
#else
static void *worker(void *unused){
#endif
 VkCtx c={0};for(int i=0;i<100;i++){
  Tex t=texture(0);if(!bind_pool_memory(&c,&t,1,64))abort();
  t=texture(0);t.f.depth=1;if(bind_pool_memory(&c,&t,1,64))abort();
 }return 0;
}
int main(int argc,char **argv){
 VkCtx c={0};Tex t;enabled=argc>2 && !strcmp(argv[2],"on");
 if(argc>1 && !strcmp(argv[1],"concurrent")){
#ifdef _WIN32
  HANDLE threads[16];for(int i=0;i<16;i++){threads[i]=CreateThread(NULL,0,worker,NULL,0,NULL);CHECK(threads[i]);}
  for(int i=0;i<16;i++){WaitForSingleObject(threads[i],INFINITE);CloseHandle(threads[i]);}
#else
  pthread_t threads[16];for(int i=0;i<16;i++)CHECK(!pthread_create(&threads[i],NULL,worker,NULL));
  for(int i=0;i<16;i++)pthread_join(threads[i],NULL);
#endif
  CHECK(queries==3200 && binds==1600 && logs==20 && colour_logs==16 && depth_logs==4);return 0;
 }
 ordered=1;
 if(argc>1 && !strcmp(argv[1],"reports")){
  t=texture(192);CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(strstr(last,"decision=unresolved") && strstr(last,"span_known=0"));
  reset();t=texture(0);no_alloc=1;CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(strstr(last,"decision=no_allocation"));
  reset();t=texture(1);CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(strstr(last,"decision=alignment") && strstr(last,"alloc_offset=1"));
  reset();t=texture(0);req.memoryTypeBits=2;CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(strstr(last,"decision=memory_type"));
  reset();t=texture(0);bind_failure=1;CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(strstr(last,"decision=bind_failed") && strstr(last,"bound=0"));
  CHECK(logs==5);return 0;
 }
 if(argc>1 && !strcmp(argv[1],"policy")){
  t=texture(0);CHECK(bind_pool_memory(&c,&t,1,64)==!enabled);
  CHECK(queries==1 && resolves==!enabled && infos==!enabled && binds==!enabled);
  CHECK(t.bound_to==(enabled?NULL:(void *)1));
  CHECK(logs==1 && strstr(last,"guest_size=64") && strstr(last,"req_size=128"));
  CHECK(strstr(last,enabled?"policy_optin":"bound"));
  reset();t=texture(64);req.size=64;
  CHECK(bind_pool_memory(&c,&t,2,64)==1 && binds==1 && t.bound_to==(void *)1);
  CHECK(logs==1);
  // A later environment mutation cannot change the cached process policy.
  int initial=enabled;enabled=!enabled;reset();t=texture(0);
  CHECK(bind_pool_memory(&c,&t,3,64)==!initial);
  CHECK(logs==2);return 0;
 }
 // Identical failure side effects and API call order with the experiment on/off.
 reset();t=texture(0);t.f.depth=1;CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(!resolves && !t.bound_to);
 reset();t=texture(0);t.f.stencil=1;CHECK(!bind_pool_memory(&c,&t,1,64));CHECK(!resolves && !t.bound_to);
 reset();t=texture(0);req.size=0;CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(!resolves && !t.bound_to);
 reset();t=texture(192);CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(resolves==1 && !infos && !t.bound_to);
 reset();t=texture(0);no_alloc=1;CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(resolves==1 && !infos && !t.bound_to);
 reset();t=texture(1);CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(resolves==1 && !infos && !t.bound_to);
 reset();t=texture(0);req.memoryTypeBits=2;CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(infos==1 && !binds && !t.bound_to);
 reset();t=texture(0);bind_failure=1;CHECK(!bind_pool_memory(&c,&t,1,128));CHECK(binds==1 && !t.bound_to);
 reset();t=texture(0);CHECK(bind_pool_memory(&c,&t,1,128));CHECK(queries==1 && resolves==1 && infos==1 && binds==1 && t.bound_to==(void *)1);
 return 0;
}
'''


class PoolBoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not cc:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            if candidate.is_file():
                cc = str(candidate)
        if not cc:
            raise unittest.SkipTest('clang required for actual C binding fixture')
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        folder = Path(cls.folder.name)
        source = folder / 'binding.c'
        source.write_text(FIXTURE + binding_source() + MAIN, encoding='utf-8')
        cls.exe = folder / ('binding.exe' if os.name == 'nt' else 'binding')
        command = [cc, '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-Wno-unused-function', str(source), '-o', str(cls.exe)]
        if os.name != 'nt':
            command.append('-pthread')
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def run_fixture(self, *args):
        result = subprocess.run([str(self.exe), *args], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_and_optin_only_change_oversized_colour_policy(self):
        self.run_fixture('policy', 'on')
        self.run_fixture('policy', 'off')

    def test_existing_failure_paths_and_exact_fit_preserve_api_sequence(self):
        self.run_fixture('failures', 'off')
        self.run_fixture('failures', 'on')

    def test_concurrent_suspicious_bindings_keep_separate_colour_and_depth_budgets(self):
        self.run_fixture('concurrent', 'off')

    def test_suspicious_failure_logs_identify_actual_decision(self):
        self.run_fixture('reports', 'off')

    @unittest.skipUnless(os.name == 'nt', 'full Windows runtime syntax fixture')
    def test_complete_texture_unit_composes_with_existing_adapters(self):
        from newsnap.adapt import adapt_sources
        from newsnap.pool_bounds_adapt import edits
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        cc = sdk / 'llvm/bin/clang.exe'
        if not cc.is_file():
            self.skipTest('bundled Windows compiler required')
        with tempfile.TemporaryDirectory() as temporary:
            staged = adapt_sources(Path(temporary) / 'source')
            path = staged / 'runtime/vk_texture.c'
            source = path.read_text(encoding='utf-8')
            for before, after in edits()['runtime/vk_texture.c']:
                if before in source:
                    self.assertEqual(source.count(before), 1)
                    source = source.replace(before, after, 1)
                else:
                    self.assertEqual(source.count(after), 1)  # Once root wires it.
            path.write_text(source, encoding='utf-8')
            command = [str(cc), '-fsyntax-only', '-Wall', '-Werror',
                       '-I' + str(staged / 'runtime'),
                       '-I' + str(sdk / 'runtime/deps/include'),
                       '-I' + str(sdk / 'runtime/deps/include/vma'), str(path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
