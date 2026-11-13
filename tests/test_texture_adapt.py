import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.texture_adapt import UPLOAD_DIAGNOSTICS, adapt_texture_source

ROOT = Path(__file__).resolve().parents[1]


class TextureDiagnosticTests(unittest.TestCase):
    def test_actual_slot_consumer_cannot_resurrect_freed_pool_descriptor(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang required for native descriptor lifetime fixture')
        donor = (ROOT / 'third_party/astral/runtime/vk_texture.c').read_text(encoding='utf-8')
        def functions(text):
            result = []
            for signature in ('void vk_texture_range_gone(', 'void vk_texture_register(',
                              'static Tex *slot_resolve(', 'const VkTexImage *vk_texture_by_id_locked('):
                start = text.index(signature)
                result.append(text[start:text.index('\n}', start) + 2])
            return '\n'.join(result)
        prelude = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
typedef void *VmaAllocation;
typedef struct { unsigned swizzle_r,swizzle_g,swizzle_b,swizzle_a; } nvn_texdesc;
typedef struct { uint64_t size; } nvn_texlayout;
typedef struct { void *mem; nvn_texdesc d; nvn_texlayout L; } tex_t;
typedef struct { uint8_t swz[4];int set_swizzle; } view_t;
typedef struct { uint64_t addr; } TexKey;
typedef struct { uint8_t swz[4]; } VkTexImage;
typedef struct Tex { VkTexImage pub;TexKey key;void *bound_to;int released;struct Tex *next_at;
 unsigned last_use,uploaded,checked; } Tex;
typedef struct { Tex *ce;uint32_t cgen,cepoch;view_t cview;uint8_t chas_view,used,has_view;view_t v;tex_t t; } TexSlot;
typedef struct { unsigned n,cap;Tex *vals[32]; } Map;
static Map by_key={.cap=32},by_addr={.cap=32};
static TexSlot *tslots;static int ntslots;
static uint64_t *sinfo;static uint32_t slots_gen,reg_serial,agen[65536],submit_epoch=1;
static int creates,refreshes;
enum {NVN_TEXTURE_SWIZZLE_R=1,NVN_TEXTURE_SWIZZLE_G=2,NVN_TEXTURE_SWIZZLE_B=3,NVN_TEXTURE_SWIZZLE_A=4};
static void lock(void){} static void unlock(void){}
static void pre_range_gone(uint64_t a,uint64_t n,int all){}
static void snap_upload_gone(uint64_t a,uint64_t n){}
static void pre_add(const tex_t *t){}
static void rt_fatal(const char *format,...) { abort(); }
static unsigned agen_idx(uint64_t a){return (unsigned)(a>>8)&65535;}
static void make_key(const tex_t *t,TexKey *k){k->addr=(uintptr_t)t->mem;}
static int same_but_swizzle(const TexKey *a,const TexKey *b){return a->addr==b->addr;}
static Tex *nvn_hm_get(Map *m,const void *key) {
 uint64_t a=*(const uint64_t*)key;
 for(int i=0;i<32;i++)if(m->vals[i]&&m->vals[i]->key.addr==a)return m->vals[i];return NULL;
}
static void destroy_tex(Tex *e) {
 for(int i=0;i<32;i++)if(by_key.vals[i]==e)by_key.vals[i]=NULL,by_key.n--;
 agen[agen_idx(e->key.addr)]++;free(e);
}
static Tex *entry_of(const tex_t *t) {
 creates++;Tex *e=calloc(1,sizeof *e);e->key.addr=(uintptr_t)t->mem;
 e->pub.swz[0]=1;e->pub.swz[1]=2;e->pub.swz[2]=3;e->pub.swz[3]=4;
 for(int i=0;i<32;i++)if(!by_key.vals[i]){by_key.vals[i]=e;by_key.n++;break;}
 return e;
}
static void make_fresh_snap(Tex *e){refreshes++;e->uploaded=1;}
'''
        main = r'''
static void reg(int id,uint64_t addr,uint64_t size) {
 tex_t t={.mem=(void*)(uintptr_t)addr,.L={size}};vk_texture_register(id,&t,NULL);
}
int main(void) {
 reg(0,0x1000,0x100);reg(1,0x3000,0x100);
 const VkTexImage *old=vk_texture_by_id_locked(0,NULL,NULL);
 const VkTexImage *live=vk_texture_by_id_locked(1,NULL,NULL);
 if(!old||!live||creates!=2)return 1;
 uint64_t token=sinfo[1];unsigned generation=slots_gen;
 vk_texture_range_gone(0x1000,0x100,NULL);
 int before=creates;
 const VkTexImage *after=vk_texture_by_id_locked(0,NULL,NULL);
#if BASELINE
 // Proves the original pinned consumer recreates the freed descriptor.
 if(!after||creates!=before+1||!tslots[0].used||!sinfo[0])return 2;
 return 0;
#else
 if(after||creates!=before||tslots[0].used||tslots[0].ce||sinfo[0])return 3;
 if(slots_gen!=generation+1||sinfo[1]!=token||vk_texture_by_id_locked(1,NULL,NULL)!=live)return 4;
 // A new registration at reused storage remains valid and obtains a new token.
 reg(0,0x1000,0x100);if(!sinfo[0]||!vk_texture_by_id_locked(0,NULL,NULL))return 5;
 // Overlap must include a descriptor starting before the retired range.
 reg(2,0xf80,0x100);reg(3,0xf00,0x100);reg(4,0x1100,0x100);
 reg(5,UINT64_MAX-15,16);reg(6,0x1000,0);
 uint64_t untouched[4]={sinfo[3],sinfo[4],sinfo[5],sinfo[6]};
 vk_texture_range_gone(0x1000,0x100,NULL);
 if(tslots[2].used||sinfo[2])return 6;
 if(!tslots[3].used||!tslots[4].used||!tslots[5].used||!tslots[6].used)return 7;
 if(sinfo[3]!=untouched[0]||sinfo[4]!=untouched[1]||sinfo[5]!=untouched[2]||sinfo[6]!=untouched[3])return 8;
 // Empty retirement has no effect; high ranges cannot wrap to low addresses.
 unsigned current=slots_gen;vk_texture_range_gone(0x3000,0,NULL);
 if(slots_gen!=current||!tslots[1].used)return 9;
 reg(7,8,32);vk_texture_range_gone(UINT64_MAX-7,8,NULL);
 if(!tslots[7].used||tslots[5].used)return 10;
 return 0;
#endif
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for label, text, baseline in (('baseline', donor, 1), ('fixed', adapt_texture_source(donor), 0)):
                source = folder / (label + '.c')
                source.write_text(prelude + functions(text) + main, encoding='utf-8')
                executable = folder / (label + ('.exe' if os.name == 'nt' else ''))
                built = subprocess.run([compiler, '-DBASELINE=' + str(baseline), str(source), '-o', str(executable)], capture_output=True)
                self.assertEqual(built.returncode, 0, built.stderr.decode(errors='replace'))
                ran = subprocess.run([str(executable)], capture_output=True)
                self.assertEqual(ran.returncode, 0, f'{label} lifetime fixture: {ran.returncode}')

    def test_pinned_source_is_patched_once_and_changed_seams_fail_closed(self):
        source = (ROOT / 'third_party/astral/runtime/vk_texture.c').read_text(encoding='utf-8')
        result = adapt_texture_source(source)
        self.assertEqual(adapt_texture_source(result), result)
        self.assertIn('snap_upload_trace(t, e->pub.addr, lv + skip, ly, rb);', result)
        self.assertIn('    snap_upload_gone(lo, size);', result)
        with self.assertRaisesRegex(ValueError, 'seam'):
            adapt_texture_source(source.replace('static void upload(Tex *e) {', 'static void upload_changed(Tex *e) {'))

    def test_real_helper_observes_unmapped_source_but_preserves_legitimate_noaccess(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            candidate = ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
            compiler = str(candidate) if candidate.is_file() else None
        if not compiler:
            self.skipTest('clang required for executable diagnostic fixture')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / 'fixture.c'
            source.write_text(r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
typedef struct { unsigned format,target,width,height,depth,levels; } nvn_texdesc;
typedef struct { uint64_t size,layer_size; } nvn_texlayout;
typedef struct { nvn_texdesc d; nvn_texlayout L; void *mem; } tex_t;
typedef struct { uint64_t base,size; unsigned state,perm; } RtMemoryInfo;
enum { PLAT_PROT_NONE,PLAT_PROT_READ,PLAT_PROT_RW };
static int enabled,logical=1,hoststate=0,logs,suspects;
static struct { uint64_t frames; } gfx_counters;
static char *fixture_getenv(const char *name) { return enabled ? "1" : NULL; }
#define getenv fixture_getenv
static void rt_log(const char *format,...) {
 logs++; if(strstr(format,"suspect")) suspects++;
}
static void nvn_tex_layout(const nvn_texdesc *d,nvn_texlayout *out) { out->size=4096;out->layer_size=4096; }
static int nvn_deswizzle_geom(const nvn_texdesc *d,unsigned l,unsigned a,uint32_t *r,uint32_t *rows,
 uint32_t *s,uint64_t *b,unsigned *th,unsigned *td,uint32_t *bpb) {
 *r=64;*rows=64;*s=1;*b=0;*th=0;*td=0;*bpb=1;return 0;
}
static int mem_query(uint64_t a,RtMemoryInfo *out) {
 *out=(RtMemoryInfo){.base=0x10000,.size=4096,.state=logical?5:0,.perm=logical?3:0};return 0;
}
static int plat_mem_state(uint64_t a,uint64_t limit,uint64_t *end) { *end=limit;return hoststate; }
''' + UPLOAD_DIAGNOSTICS + r'''
int main(void) {
 tex_t t={.L={4096,4096},.mem=(void*)0x10000,.d={.width=64,.height=64,.levels=1}};
 snap_upload_trace(&t,0x10000,0,0,64); if(logs||snap_upload_count) return 1;
 enabled=1;
 // Valid logical memory can be host NOACCESS while a mirror owns a hold.
 snap_upload_trace(&t,0x10000,0,0,64); if(suspects||snap_upload_count!=1) return 2;
 snap_upload_gone(0x10000,4096); if(snap_upload_count!=2) return 3;
 logical=0; snap_upload_trace(&t,0x10000,0,0,64); if(suspects!=1) return 4;
 logical=1; hoststate=-1; snap_upload_trace(&t,0x10000,0,0,64); if(suspects!=2) return 5;
 // Ring is bounded even when history advances beyond its capacity.
 hoststate=2; for(int i=0;i<250;i++) snap_upload_trace(&t,0x10000,0,0,64);
 if(snap_upload_count!=254||sizeof(snap_upload_ring)/sizeof(*snap_upload_ring)!=200) return 6;
 return 0;
}
''', encoding='utf-8')
            executable = folder / ('fixture.exe' if os.name == 'nt' else 'fixture')
            subprocess.run([compiler, str(source), '-o', str(executable)], check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
