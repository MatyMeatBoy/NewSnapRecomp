from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

from newsnap.color_transfer_adapt import edits

ROOT = Path(__file__).resolve().parents[1]


class ColorTransferTests(unittest.TestCase):
    def test_actual_color_record_preserves_encoded_source_and_neutral_fast_paths(self):
        sdk = ROOT / 'toolchain/astral-release/Astral Chain-Setup'
        if not (sdk / 'runtime/deps/include/vulkan/vulkan.h').is_file():
            self.skipTest('bundled Vulkan headers required for native color-transfer fixture')
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(sdk / 'llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang required for native color-transfer fixture')
        source = (ROOT / 'third_party/astral/runtime/vk_color.c').read_text(encoding='utf-8')
        for old, new in edits()['runtime/vk_color.c']:
            self.assertEqual(source.count(old), 1)
            source = source.replace(old, new, 1)
        def function(signature):
            start = source.index(signature)
            return source[start:source.index('\n}', start) + 2]
        state = source[source.index('static struct {'):source.index('} C = {.seen = ~0u};') + len('} C = {.seen = ~0u};')]
        prelude = r'''
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
typedef void *VmaAllocation;
#define SLOTS 8
typedef struct { VkDevice device; } VkCtx;
static VkCtx context;
static int dispatches,views,pushes,barriers;
static VkFormat view_format;
static float coefficients[4];
static unsigned version=1;
static double gamma_value=1;
static VkCtx *vk_ctx(void) {return &context;}
static void rt_log(const char *format,...) {}
static unsigned cfg_version(void) {return version;}
static double cfg_double(const char *name) {
 return strstr(name,"GAMMA")?gamma_value:strstr(name,"BRIGHTNESS")?0:100;
}
static void vkDestroyImageView(VkDevice d,VkImageView v,const VkAllocationCallbacks *a) {}
static VkResult vkCreateImageView(VkDevice d,const VkImageViewCreateInfo *vi,const VkAllocationCallbacks *a,VkImageView *out) {
 views++;view_format=vi->format;*out=(VkImageView)(uintptr_t)21;return VK_SUCCESS;
}
static void vkCmdBindPipeline(VkCommandBuffer c,VkPipelineBindPoint b,VkPipeline p) {}
static void vkCmdDispatch(VkCommandBuffer c,uint32_t x,uint32_t y,uint32_t z) {dispatches++;}
static void vkCmdPushConstants(VkCommandBuffer c,VkPipelineLayout l,VkShaderStageFlags f,uint32_t o,uint32_t n,const void *v) {
 pushes++;memcpy(coefficients,(const char*)v+16,16);
}
static void vkCmdPipelineBarrier2(VkCommandBuffer c,const VkDependencyInfo *i) {barriers++;}
static void rec_push(PFN_vkCmdPushDescriptorSetKHR f,VkCommandBuffer c,VkPipelineBindPoint b,VkPipelineLayout l,
 uint32_t first,uint32_t n,const VkWriteDescriptorSet *w) {}
'''
        helpers = r'''
static int init(VkCtx *c) {C.tried=C.ok=1;C.img=(VkImage)(uintptr_t)123;return 1;}
static int ensure_image(VkCtx *c,uint32_t w,uint32_t h) {return 1;}
'''
        main = r'''
int main(void) {
 int crop[4]={0,0,1920,1080};VkImage src=(VkImage)(uintptr_t)11;VkCommandBuffer cb=(VkCommandBuffer)(uintptr_t)1;
 VkFormat formats[4]={VK_FORMAT_R8G8B8A8_UNORM,VK_FORMAT_R8G8B8A8_SRGB,
                       VK_FORMAT_B8G8R8A8_UNORM,VK_FORMAT_B8G8R8A8_SRGB};
 // All RGBA/BGRA pairs: preserve encoded bytes by matching source-view and
 // destination transfer classes, including an sRGB-only surface fallback.
 for(int source=0;source<4;source++)for(int destination=0;destination<4;destination++) {
  int before=dispatches,old_views=views,old_barriers=barriers;
  VkImage result=vk_color_record(cb,0,src,formats[source],formats[destination],crop);
  int needs_copy=(source%2)!=(destination%2);
  if(!needs_copy) {if(result||dispatches!=before||views!=old_views)return 1;}
  else {
   if(!result||dispatches!=before+1||views!=old_views+1||barriers!=old_barriers+4)return 2;
   if(view_format!=formats[(source/2)*2+destination%2])return 3;
   if(coefficients[0]!=0||coefficients[1]!=1||coefficients[2]!=1||coefficients[3]!=1)return 4;
  }
 }
 // Unknown and floating-point formats retain their previous transfer semantics.
 int before=dispatches;
 if(vk_color_record(cb,0,src,VK_FORMAT_R16G16B16A16_SFLOAT,VK_FORMAT_B8G8R8A8_SRGB,crop))return 5;
 if(vk_color_record(cb,0,src,VK_FORMAT_R8G8B8A8_SRGB,VK_FORMAT_R16G16B16A16_SFLOAT,crop))return 6;
 if(dispatches!=before)return 7;
 // Existing adjustment coefficients, when supplied, are passed through intact.
 version++;gamma_value=2;
 if(!vk_color_record(cb,0,src,VK_FORMAT_R8G8B8A8_UNORM,VK_FORMAT_B8G8R8A8_UNORM,crop)||coefficients[3]!=2)return 8;
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = folder / 'color.c'
            fixture.write_text(prelude + state + helpers + function('static int adjusting(') +
                               function('static void barrier(') + function('static VkFormat snap_present_encoded_format(') +
                               function('VkImage vk_color_record(') + main, encoding='utf-8')
            executable = folder / ('color.exe' if os.name == 'nt' else 'color')
            result = subprocess.run([compiler, '-I', str(sdk / 'runtime/deps/include'), str(fixture), '-o', str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            result = subprocess.run([str(executable)], capture_output=True)
            self.assertEqual(result.returncode, 0, 'native color transfer fixture exit ' + str(result.returncode))


if __name__ == '__main__':
    unittest.main()
