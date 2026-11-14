import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.photo_readback_adapt import GPU, CPU, IMPORT_SUPPORT, edits

ROOT = Path(__file__).resolve().parents[1]


class PhotoReadbackTests(unittest.TestCase):
    def test_actual_import_report_has_a_concurrent_eight_message_limit(self):
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native concurrent diagnostic fixture')
        fixture = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdarg.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <pthread.h>
#endif
typedef struct { struct { struct { unsigned propertyFlags; } memoryTypes[2]; } mem_props; } VkCtx;
static int shadow_on,enabled,messages,start;
static VkCtx context={.mem_props.memoryTypes={{6},{10}}};
static const char *fixture_getenv(const char *name){return enabled?"fixture":NULL;}
#define getenv fixture_getenv
static void rt_log(const char *format,...){__atomic_fetch_add(&messages,1,__ATOMIC_RELAXED);}
''' + IMPORT_SUPPORT + r'''
#ifdef _WIN32
static DWORD WINAPI worker(void *argument) {
#else
static void *worker(void *argument) {
#endif
 while(!__atomic_load_n(&start,__ATOMIC_ACQUIRE)) {}
 for(int i=0;i<1000;i++)snap_import_report(&context,i%2,3,4096);
 return 0;
}
int main(void){
 for(int i=0;i<10;i++)snap_import_report(&context,0,3,4096);
 if(messages)return 1;
 enabled=1;
#ifdef _WIN32
 HANDLE threads[32];
 for(int i=0;i<32;i++){threads[i]=CreateThread(NULL,0,worker,NULL,0,NULL);if(!threads[i])return 2;}
#else
 pthread_t threads[32];
 for(int i=0;i<32;i++)if(pthread_create(&threads[i],NULL,worker,NULL))return 2;
#endif
 __atomic_store_n(&start,1,__ATOMIC_RELEASE);
 for(int i=0;i<32;i++){
#ifdef _WIN32
  WaitForSingleObject(threads[i],INFINITE);CloseHandle(threads[i]);
#else
  pthread_join(threads[i],NULL);
#endif
 }
 if(messages!=8)return 3;
 for(int i=0;i<10;i++)snap_import_report(&context,-1,3,4096);
 return messages==8?0:4;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'concurrent.c'
            source.write_text(fixture, encoding='utf-8')
            executable = folder / ('concurrent.exe' if os.name == 'nt' else 'concurrent')
            command = [compiler, str(source), '-o', str(executable)]
            if os.name != 'nt':
                command.append('-pthread')
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            for _ in range(20):
                result = subprocess.run([str(executable)], capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 0, 'concurrent diagnostic fixture exit ' + str(result.returncode))

    def test_actual_import_allocator_falls_back_to_managed_noncoherent_storage(self):
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        if not (sdk / 'runtime/deps/include/vulkan/vulkan.h').is_file():
            self.skipTest('bundled Vulkan headers required for native import fixture')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native import fixture')
        donor = (ROOT / 'third_party/astral/runtime/vk_memory.c').read_text(encoding='utf-8')
        fixed = donor
        for old, new in edits().get('runtime/vk_memory.c', []):
            self.assertEqual(fixed.count(old), 1)
            fixed = fixed.replace(old, new, 1)
        def functions(text):
            selected = []
            signatures = ['static int memory_type(', 'static int import_pool(', 'int vk_mem_resolve(',
                          'static void shadow_fetch(']
            if 'static int snap_shadow_active(' in text:
                signatures.append('static int snap_shadow_active(')
            signatures += ['void vk_mem_shadow_sync(', 'void vk_mem_gpu_pending(']
            for signature in signatures:
                start = text.index(signature)
                selected.append(text[start:text.index('\n}', start) + 2])
            return '\n'.join(selected)
        prelude = r'''
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
typedef struct { VkDevice device;void *vma;VkPhysicalDeviceMemoryProperties mem_props;uint64_t min_imported_host_alignment; } VkCtx;
typedef struct { VkBuffer buf;VkDeviceMemory mem;uint64_t import_lo,import_hi;uint8_t *smap;int stouched;void *salloc; } PoolRec;
typedef struct { VkBuffer buffer;uint64_t offset,avail,alloc_offset;void *alloc,*pool;unsigned cls; } VkMemSpan;
typedef struct { uint64_t gen,lo,hi,base,end;VkBuffer buf;void *alloc,*pool;unsigned cls; } ResolveHit;
static int shadow_on,n_imports,shadow_calls,manual_allocations,unsafe_allocations,touches,allow_shadow=1;
static volatile int32_t snap_shadow_fallback;
static uint64_t pool_gen=1;static ResolveHit hit;
static uint32_t selected_flags,selected_type;
static uint8_t shadow_cache[4096],gpu_backing[4096];static int invalidations;
static PoolRec *stouch[8];static int nstouch,synced,shadow_lock,gen_lock;
static uint64_t s_syncs,s_ticks;
typedef struct { uint64_t lo,hi; } SRange;
static SRange spend_storage[8],*spend=spend_storage;static int nspend,cspend=8;
static uint64_t qpc(void){return 0;}
static void plat_mutex_lock(int *lock){}static void plat_mutex_unlock(int *lock){}
static void grow(void **p,int *c,size_t n){abort();}
static void shadow_sync_pool(PoolRec *r){if(!r->smap)abort();synced++;}
static void rt_log(const char *format,...){}
static void snap_import_report(const VkCtx *c,int type,uint32_t bits,uint64_t alignment){}
static void rt_fatal(const char *format,...){abort();}
static int plat_inc32(int *value){return ++*value;}
static VkBufferUsageFlags pool_usage(const VkCtx *c){return VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT;}
static VkResult host_properties(VkDevice d,VkExternalMemoryHandleTypeFlagBits t,const void *host,VkMemoryHostPointerPropertiesEXT *p){p->memoryTypeBits=1;return VK_SUCCESS;}
static PFN_vkGetMemoryHostPointerPropertiesEXT p_host_props=host_properties;
static PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice d,const char *name){return NULL;}
static VkResult vkCreateBuffer(VkDevice d,const VkBufferCreateInfo *i,const VkAllocationCallbacks *a,VkBuffer *b){*b=(VkBuffer)(uintptr_t)1;return VK_SUCCESS;}
static void vkGetBufferMemoryRequirements(VkDevice d,VkBuffer b,VkMemoryRequirements *r){*r=(VkMemoryRequirements){.size=4096,.memoryTypeBits=1};}
static VkCtx *current;
static VkCtx *vk_ctx(void){return current;}
// Noncoherent-driver model: cached bytes remain stale until invalidated.
static void vmaInvalidateAllocation(void *vma,void *alloc,VkDeviceSize offset,VkDeviceSize n){
 invalidations++;memcpy((uint8_t*)alloc+offset,gpu_backing+offset,(size_t)n);
}
static VkResult vkAllocateMemory(VkDevice d,const VkMemoryAllocateInfo *i,const VkAllocationCallbacks *a,VkDeviceMemory *m){
 manual_allocations++;selected_type=i->memoryTypeIndex;selected_flags=current->mem_props.memoryTypes[selected_type].propertyFlags;
 if((selected_flags&6)!=6)unsafe_allocations++;*m=(VkDeviceMemory)(uintptr_t)2;return VK_SUCCESS;
}
static VkResult vkBindBufferMemory(VkDevice d,VkBuffer b,VkDeviceMemory m,VkDeviceSize offset){return VK_SUCCESS;}
static void vkDestroyBuffer(VkDevice d,VkBuffer b,const VkAllocationCallbacks *a){}
static void vkFreeMemory(VkDevice d,VkDeviceMemory m,const VkAllocationCallbacks *a){}
static int shadow_pool(VkCtx *c,PoolRec *r,uint64_t a,uint64_t n){
 shadow_calls++;if(!allow_shadow)return 0;
 r->smap=shadow_cache;r->salloc=shadow_cache;r->buf=(VkBuffer)(uintptr_t)3;r->import_lo=a;r->import_hi=a+n;return 1;
}
static ResolveHit *rhit_slot(uint64_t a){return &hit;}
static int resolve_check_on(void){return 0;}
static int resolve_locked(uint64_t a,uint64_t n,VkMemSpan *s){return 0;}
static void shadow_touch(PoolRec *r){if(!r->smap)abort();touches++;r->stouched=1;stouch[nstouch++]=r;}
'''
        main = r'''
static void cache(PoolRec *r,uint64_t a) {
 hit=(ResolveHit){.gen=1,.lo=a,.hi=a+4096,.base=a,.end=a+4096,.buf=r->buf,.pool=r};
}
int main(void) {
 VkCtx context={.min_imported_host_alignment=4096};current=&context;
 context.mem_props.memoryTypeCount=2;
 context.mem_props.memoryTypes[0].propertyFlags=6;
 context.mem_props.memoryTypes[1].propertyFlags=6;
 PoolRec coherent={0};if(!import_pool(&context,&coherent,0x10000,4096)||manual_allocations!=1||selected_flags!=6)return 1;
 // Driver exposes only a cached, noncoherent type for this imported pointer.
 context.mem_props.memoryTypes[0].propertyFlags=10;
 PoolRec cached={0};if(!import_pool(&context,&cached,0x20000,4096))return 2;
#if BASELINE
 // Pinned legacy implementation silently allocates noncoherent manual import,
 // which has no mapping/cache-maintenance path. Positive coherent case above
 // proves the fixture is not rejecting every import.
 if(manual_allocations!=2||unsafe_allocations!=1||selected_flags!=10||shadow_calls)return 3;
 return 0;
#else
 if(manual_allocations!=1||unsafe_allocations||shadow_calls!=1||!cached.smap||!snap_shadow_fallback)return 4;
 if(shadow_on)return 5; // A fallback must not force all future pools to shadows.
 // A pre-existing direct import remains direct and is never shadow-touched.
 VkMemSpan span;cache(&coherent,0x10000);
 if(!vk_mem_resolve(0x10000,64,&span)||touches)return 6;
 cache(&cached,0x20000);
 if(!vk_mem_resolve(0x20000,64,&span)||touches!=1)return 7;
 vk_mem_shadow_sync();if(synced!=1||cached.stouched)return 11;
 vk_mem_gpu_pending(0x20000,64);if(nspend!=1||spend[0].lo!=0x20000||spend[0].hi!=0x20040)return 12;
 // The real managed readback fetch invalidates cached backing before copying.
 memset(shadow_cache,0,sizeof shadow_cache);memset(gpu_backing,0x6a,sizeof gpu_backing);
 uint8_t fetched[64]={0};shadow_fetch(&cached,0x20000,sizeof fetched,fetched);
 if(invalidations!=1||memcmp(fetched,gpu_backing,sizeof fetched))return 13;
 // New coherent imports still take the original fast path after a fallback.
 context.mem_props.memoryTypes[0].propertyFlags=6;
 PoolRec later={0};if(!import_pool(&context,&later,0x30000,4096)||manual_allocations!=2||later.smap)return 8;
 // Non-host-visible imported payloads may not remain CPU-accessible either.
 context.mem_props.memoryTypes[0].propertyFlags=1;
 PoolRec device_only={0};if(!import_pool(&context,&device_only,0x40000,4096)||manual_allocations!=2||!device_only.smap)return 9;
 // Managed allocation failure must not fall back to an unsafe manual import.
 allow_shadow=0;snap_shadow_fallback=0;
 PoolRec failed={0};if(import_pool(&context,&failed,0x50000,4096)||manual_allocations!=2||snap_shadow_fallback)return 10;
 return 0;
#endif
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for label, text, baseline in (('baseline', donor, 1), ('fixed', fixed, 0)):
                fixture = folder / (label + '.c')
                fixture.write_text(prelude + functions(text) + main, encoding='utf-8')
                executable = folder / (label + ('.exe' if os.name == 'nt' else ''))
                result = subprocess.run([compiler, '-DBASELINE=' + str(baseline), '-I', str(sdk / 'runtime/deps/include'),
                                         str(fixture), '-o', str(executable)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
                result = subprocess.run([str(executable)], capture_output=True)
                self.assertEqual(result.returncode, 0, label + ' native import fixture exit ' + str(result.returncode))

    def test_exact_seams_and_owned_staging_capture_with_padded_rows(self):
        for name, changes in edits().items():
            source = (ROOT / 'third_party/astral' / name).read_text(encoding='utf-8')
            for old, new in changes:
                self.assertEqual(source.count(old), 1, name)
                source = source.replace(old, new, 1)
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        if not (sdk / 'runtime/deps/include/vulkan/vulkan.h').is_file():
            self.skipTest('bundled Vulkan headers required for native readback fixture')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native readback fixture')
        prelude = r'''
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
typedef void *VmaAllocation;
typedef struct { void *vma; } VkCtx;
typedef struct { VkImage image;VkFormat format;unsigned samples;uint64_t addr; } VkTexImage;
typedef struct { VkTexImage *img;unsigned nz,w,h;int x,y; } Sub;
typedef struct { VkCommandBuffer cb;uint64_t fence;unsigned recorded; } VkExec;
typedef struct { VkBuffer buffer;uint64_t offset; } VkMemSpan;
static struct { uint64_t frames; } gfx_counters={123};
static VkCtx context;
static int enabled,allocations,destroyed,files,copies;
static uint8_t first_pixel[4];
static char logline[2048];
static void (*pending_fn)(void*);static void *pending_arg;
static char *fixture_getenv(const char *name){return enabled?"fixture":NULL;}
#define getenv fixture_getenv
static VkCtx *vk_ctx(void){return &context;}
static void plat_file_mkdir_p(const char *path){}
static void rt_log(const char *format,...) {
 va_list a;va_start(a,format);vsnprintf(logline,sizeof logline,format,a);va_end(a);
}
static void rt_write_png(const char *path,const uint8_t *rgba,uint32_t w,uint32_t h) {
 files++;if(strstr(path,"source"))memcpy(first_pixel,rgba,4);
}
static void *vk_staging(VkDeviceSize size,VkBuffer *buffer,VmaAllocation *alloc) {
 void *data=calloc(1,(size_t)size);*buffer=(VkBuffer)(uintptr_t)data;*alloc=data;allocations++;return data;
}
static void vmaInvalidateAllocation(void *vma,void *alloc,uint64_t a,uint64_t n){}
static void vmaDestroyBuffer(void *vma,VkBuffer buffer,void *alloc){destroyed++;free(alloc);}
static void vkCmdCopyImageToBuffer(VkCommandBuffer cb,VkImage image,VkImageLayout layout,VkBuffer buffer,
 uint32_t count,const VkBufferImageCopy *copy) {
 copies++;memcpy((void*)(uintptr_t)buffer,(void*)(uintptr_t)image,
  (size_t)copy->imageExtent.width*copy->imageExtent.height*4);
}
static void vkCmdPipelineBarrier2(VkCommandBuffer cb,const VkDependencyInfo *info){}
static void vkCmdCopyBuffer(VkCommandBuffer cb,VkBuffer source,VkBuffer destination,uint32_t n,const VkBufferCopy *copy) {
 copies++;memcpy((uint8_t*)(uintptr_t)destination+copy->dstOffset,
  (uint8_t*)(uintptr_t)source+copy->srcOffset,(size_t)copy->size);
}
static void vk_completion_add(uint64_t fence,void(*function)(void*),void *argument){pending_fn=function;pending_arg=argument;}
'''
        main = r'''
int main(void) {
 enum {W=128,H=96,PITCH=W*4+8};
 uint8_t source[W*H*4],buffer[PITCH*H+16];
 memset(buffer,0xa5,sizeof buffer);
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  uint8_t *p=source+((size_t)y*W+x)*4;p[0]=17;p[1]=(uint8_t)(y+1);p[2]=88;p[3]=255;
 }
 for(int y=0;y<H;y++)memcpy(buffer+16+(size_t)y*PITCH,source+(size_t)y*W*4,W*4);
 VkTexImage image={.image=(VkImage)(uintptr_t)source,.format=VK_FORMAT_B8G8R8A8_UNORM,.samples=1,.addr=0x10000};
 Sub s={.img=&image,.nz=1,.w=W,.h=H};VkExec ex={.fence=4};
 VkMemSpan destination={.buffer=(VkBuffer)(uintptr_t)buffer,.offset=16};
 VkBufferImageCopy region={.bufferOffset=16,.bufferRowLength=PITCH/4,.imageExtent={W,H,1}};
 uint64_t size=PITCH*(H-1)+W*4;
 // No setting: the copy statistics still reach the log, without any file.
 snap_photo_trace_t2b(&ex,&s,size,&region,&destination);
 if(files||copies!=2||allocations!=2||ex.recorded!=2||!pending_fn)return 1;
 pending_fn(pending_arg);pending_fn=NULL;
 if(files||destroyed!=2||!strstr(logline,"mismatch_bytes=0")||!strstr(logline,"black_rows=0/0")||
    !strstr(logline,"black_tiles16=0/0 of 48")||!strstr(logline,"[none] (log only)"))return 7;
 enabled=1;snap_photo_trace_t2b(&ex,&s,size,&region,&destination);
 if(files||copies!=4||allocations!=4||ex.recorded!=4||!pending_fn)return 2;
 pending_fn(pending_arg);pending_fn=NULL;
 if(files!=2||destroyed!=4||!strstr(logline,"mismatch_bytes=0")||!strstr(logline,"black_rows=0/0"))return 3;
 if(first_pixel[0]!=88||first_pixel[1]!=1||first_pixel[2]!=17||first_pixel[3]!=255)return 4;
 // Deliberately corrupt one padded destination row. Source staging stays intact.
 memset(buffer+16+17*PITCH,0,W*4);
 snap_photo_trace_t2b(&ex,&s,size,&region,&destination);pending_fn(pending_arg);
 if(strstr(logline,"mismatch_bytes=0")||!strstr(logline,"black_rows=0/1"))return 5;
 // A band over part of the rows 32..47: no fully black row more, one run of black tiles in the buffer only.
 memset(buffer+16+32*PITCH,0,PITCH*16);
 for(int y=32;y<48;y++)memset(buffer+16+(size_t)y*PITCH,0x40,16*4);
 snap_photo_trace_t2b(&ex,&s,size,&region,&destination);pending_fn(pending_arg);
 if(!strstr(logline,"black_rows=0/1")||!strstr(logline,"black_tiles16=0/7 of 48")||
    !strstr(logline,"buffer_black_runs=1 [y32:x16-127]"))return 8;
 // Four more captures reach the cap of eight with files; the ninth adds no allocations or GPU work.
 for(int i=0;i<4;i++){snap_photo_trace_t2b(&ex,&s,size,&region,&destination);pending_fn(pending_arg);}
 int old=allocations;snap_photo_trace_t2b(&ex,&s,size,&region,&destination);
 if(allocations!=old||allocations!=16||destroyed!=16||files!=14)return 6;
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = folder / 'photo.c'
            fixture.write_text(prelude + GPU + main, encoding='utf-8')
            executable = folder / ('photo.exe' if os.name == 'nt' else 'photo')
            result = subprocess.run([compiler, '-I', str(sdk / 'runtime/deps/include'), str(fixture), '-o', str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            result = subprocess.run([str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, 'native readback fixture exit ' + str(result.returncode))
            cpu_types = r'''
typedef struct { VkTexImage pub; } Tex;
typedef struct { int nz,bw,bh,bpb;size_t wb,row; } Region;
typedef struct { int width,height; } NVNcopyRegion;
'''
            cpu_main = r'''
int main(void) {
 enum {W=128,H=96,PITCH=W*4+8};uint8_t source[W*H*4],output[PITCH*H];
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  uint8_t *p=source+((size_t)y*W+x)*4;p[0]=17;p[1]=(uint8_t)(y+1);p[2]=88;p[3]=255;
 }
 for(int y=0;y<H;y++)memcpy(output+(size_t)y*PITCH,source+(size_t)y*W*4,W*4);
 Tex texture={.pub={.format=VK_FORMAT_R8G8B8A8_SRGB}};
 Region geometry={.nz=1,.bw=1,.bh=1,.bpb=4,.wb=W*4,.row=PITCH};
 NVNcopyRegion region={W,H};
 snap_photo_trace_cpu(&texture,&geometry,&region,source,output);if(files)return 1;
 enabled=1;snap_photo_trace_cpu(&texture,&geometry,&region,source,output);
 if(files!=2||!strstr(logline,"mismatch_bytes=0")||!strstr(logline,"black_rows=0/0"))return 2;
 if(first_pixel[0]!=17||first_pixel[1]!=1||first_pixel[2]!=88||first_pixel[3]!=255)return 3;
 memset(output+17*PITCH,0,W*4);snap_photo_trace_cpu(&texture,&geometry,&region,source,output);
 if(!strstr(logline,"black_rows=0/1"))return 4;
 geometry.nz=2;snap_photo_trace_cpu(&texture,&geometry,&region,source,output);if(files!=4)return 5;
 return 0;
}
'''
            fixture.write_text(prelude + cpu_types + CPU + cpu_main, encoding='utf-8')
            result = subprocess.run([compiler, '-I', str(sdk / 'runtime/deps/include'), str(fixture), '-o', str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            result = subprocess.run([str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, 'native CPU readback fixture exit ' + str(result.returncode))


if __name__ == '__main__':
    unittest.main()
