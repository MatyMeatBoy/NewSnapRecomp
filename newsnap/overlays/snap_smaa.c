// AA-04: SMAA 1x for New Pokémon Snap, the way Ryujinx offers it (Low, Medium, High, Ultra; High by default).
//
// Snap draws no anti-aliasing of its own: after the scene, one pass tonemaps it through a 3D LUT into an RGBA8 sRGB
// target of the game's size, and the HUD is drawn straight over that target (measured: frame dump, passes 11 and 12).
// So at the start of the pass after that tonemap pass (vk_exec_pass_begin, outside any render pass), the picture is
// finished and has no HUD yet: SMAA runs on it there, in three compute passes, the official SMAA.hlsl (Jimenez et
// al., MIT; runtime/shaders/smaa_*.comp):
//   1. luma edges from the picture read through a UNORM view (gamma-encoded, as SMAA wants for edge detection),
//   2. blend weights from the edges and SMAA's area and search textures (smaa_area_tex.h, smaa_search_tex.h),
//   3. neighbourhood blending in linear light (an sRGB view), encoded back to sRGB into a work image,
// then the work image is copied over the picture and the game draws its HUD on it, sharp as before.
//
// AC_ANTI_ALIASING = off | low | medium | high | ultra (smaa, the value of earlier versions, reads as high). While an
// upscaler (FSR, DLSS) resolves the scene, SMAA stays out: its picture is anti-aliased already. Supersampling works
// together with it: SMAA runs at the enlarged size, before the reduction to the window.
#include <string.h>
#include "cfg.h"
#include "host.h"
#include "vk.h"
#include "vk_exec.h"
#include "vk_rec.h"
#include "smaa_area_tex.h"
#include "smaa_search_tex.h"
#include "smaa_blend_spv.h"
#include "smaa_edges_low_spv.h"
#include "smaa_edges_medium_spv.h"
#include "smaa_edges_high_spv.h"
#include "smaa_edges_ultra_spv.h"
#include "smaa_weights_low_spv.h"
#include "smaa_weights_medium_spv.h"
#include "smaa_weights_high_spv.h"
#include "smaa_weights_ultra_spv.h"

const char *vk_dlaa_running(void);

enum { Q_LOW, Q_MEDIUM, Q_HIGH, Q_ULTRA, NQ };

typedef struct { VkImage img; VmaAllocation mem; VkImageView view; } Work;

static struct {
    int tried, ok;
    VkDescriptorSetLayout dsl[3];
    VkPipelineLayout lay[3];   // edges (2 bindings), weights (4), blend (3)
    VkPipeline edges[NQ], weights[NQ], blend;
    VkSampler linear, point;
    Work area, search;
    int luts_ready;
    Work work[3];   // edges, weights, the blended picture
    uint32_t w, h;
    // the candidate: the last pass began on a tonemap target (one RGBA8 sRGB colour target of the game's size)
    VkExecTarget cand;
    uint64_t cand_fence;
    int have_cand;
    unsigned runs, logged;
} S;

static VkPipeline make(VkCtx *c, VkPipelineLayout lay, const uint32_t *code, size_t size) {
    VkShaderModuleCreateInfo mi = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, .codeSize = size, .pCode = code};
    VkShaderModule m = VK_NULL_HANDLE;
    if (vkCreateShaderModule(c->device, &mi, NULL, &m) != VK_SUCCESS) return VK_NULL_HANDLE;
    VkComputePipelineCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
                                      .stage = {.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                                                .stage = VK_SHADER_STAGE_COMPUTE_BIT, .module = m, .pName = "main"},
                                      .layout = lay};
    VkPipeline p = VK_NULL_HANDLE;
    if (vkCreateComputePipelines(c->device, VK_NULL_HANDLE, 1, &ci, NULL, &p) != VK_SUCCESS) p = VK_NULL_HANDLE;
    vkDestroyShaderModule(c->device, m, NULL);
    return p;
}

static int layout_of(VkCtx *c, int i, uint32_t samplers) {
    VkDescriptorSetLayoutBinding b[4];
    for (uint32_t k = 0; k <= samplers; k++)
        b[k] = (VkDescriptorSetLayoutBinding){.binding = k, .descriptorCount = 1, .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT,
                                              .descriptorType = k < samplers ? VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
                                                                             : VK_DESCRIPTOR_TYPE_STORAGE_IMAGE};
    VkDescriptorSetLayoutCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
                                           .flags = VK_DESCRIPTOR_SET_LAYOUT_CREATE_PUSH_DESCRIPTOR_BIT_KHR,
                                           .bindingCount = samplers + 1, .pBindings = b};
    VkPushConstantRange pr = {VK_SHADER_STAGE_COMPUTE_BIT, 0, 16};
    VkPipelineLayoutCreateInfo li = {.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO, .setLayoutCount = 1,
                                     .pSetLayouts = &S.dsl[i], .pushConstantRangeCount = 1, .pPushConstantRanges = &pr};
    return vkCreateDescriptorSetLayout(c->device, &dci, NULL, &S.dsl[i]) == VK_SUCCESS &&
           vkCreatePipelineLayout(c->device, &li, NULL, &S.lay[i]) == VK_SUCCESS;
}

static int init(VkCtx *c) {
    if (!vk_pipeline_push_fn()) return 0;
    VkSamplerCreateInfo si = {.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO, .magFilter = VK_FILTER_LINEAR,
                              .minFilter = VK_FILTER_LINEAR, .mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST,
                              .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
                              .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
                              .addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE, .maxLod = 0};
    if (vkCreateSampler(c->device, &si, NULL, &S.linear) != VK_SUCCESS) return 0;
    si.magFilter = si.minFilter = VK_FILTER_NEAREST;
    if (vkCreateSampler(c->device, &si, NULL, &S.point) != VK_SUCCESS) return 0;
    if (!layout_of(c, 0, 1) || !layout_of(c, 1, 3) || !layout_of(c, 2, 2)) return 0;
    static const struct { const uint32_t *e, *w; size_t es, ws; } q[NQ] = {
        {smaa_edges_low_spv, smaa_weights_low_spv, sizeof smaa_edges_low_spv, sizeof smaa_weights_low_spv},
        {smaa_edges_medium_spv, smaa_weights_medium_spv, sizeof smaa_edges_medium_spv, sizeof smaa_weights_medium_spv},
        {smaa_edges_high_spv, smaa_weights_high_spv, sizeof smaa_edges_high_spv, sizeof smaa_weights_high_spv},
        {smaa_edges_ultra_spv, smaa_weights_ultra_spv, sizeof smaa_edges_ultra_spv, sizeof smaa_weights_ultra_spv}};
    for (int i = 0; i < NQ; i++)
        if (!(S.edges[i] = make(c, S.lay[0], q[i].e, q[i].es)) || !(S.weights[i] = make(c, S.lay[1], q[i].w, q[i].ws)))
            return 0;
    if (!(S.blend = make(c, S.lay[2], smaa_blend_spv, sizeof smaa_blend_spv))) return 0;
    rt_log("smaa: ready (Low, Medium, High, Ultra)");
    return 1;
}

static int image(VkCtx *c, Work *o, VkFormat f, uint32_t w, uint32_t h, VkImageUsageFlags usage) {
    VkImageCreateInfo ii = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D, .format = f,
                            .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT,
                            .tiling = VK_IMAGE_TILING_OPTIMAL, .usage = usage, .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &ii, &ai, &o->img, &o->mem, NULL) != VK_SUCCESS) return o->img = VK_NULL_HANDLE, 0;
    VkImageViewCreateInfo vi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = o->img,
                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = f,
                                .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &vi, NULL, &o->view) != VK_SUCCESS) return o->view = VK_NULL_HANDLE, 0;
    return 1;
}

static void to_general(VkCommandBuffer cb, VkImage img, VkImageLayout from) {
    VkImageMemoryBarrier2 b = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
                               .srcStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                               .srcAccessMask = VK_ACCESS_2_MEMORY_WRITE_BIT,
                               .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                               .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT,
                               .oldLayout = from, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                               .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                               .image = img, .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    VkDependencyInfo d = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &b};
    vkCmdPipelineBarrier2(cb, &d);
}

static void all_done(VkCommandBuffer cb) {   // every earlier write visible to every later read and write
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                           .srcAccessMask = VK_ACCESS_2_MEMORY_WRITE_BIT, .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                           .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT};
    VkDependencyInfo d = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &d);
}

// SMAA's two fixed textures, uploaded once through the replay's command buffer.
static int luts(VkCtx *c, VkCommandBuffer cb) {
    if (S.luts_ready) return 1;
    if (!image(c, &S.area, VK_FORMAT_R8G8_UNORM, AREATEX_WIDTH, AREATEX_HEIGHT,
               VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT) ||
        !image(c, &S.search, VK_FORMAT_R8_UNORM, SEARCHTEX_WIDTH, SEARCHTEX_HEIGHT,
               VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT))
        return 0;
    VkBuffer buf;
    VmaAllocation mem;
    uint8_t *map = vk_staging(sizeof areaTexBytes + sizeof searchTexBytes, &buf, &mem);
    if (!map) return 0;
    memcpy(map, areaTexBytes, sizeof areaTexBytes);
    memcpy(map + sizeof areaTexBytes, searchTexBytes, sizeof searchTexBytes);
    vmaFlushAllocation(c->vma, mem, 0, VK_WHOLE_SIZE);
    to_general(cb, S.area.img, VK_IMAGE_LAYOUT_UNDEFINED);
    to_general(cb, S.search.img, VK_IMAGE_LAYOUT_UNDEFINED);
    VkBufferImageCopy a = {.bufferOffset = 0, .imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                           .imageExtent = {AREATEX_WIDTH, AREATEX_HEIGHT, 1}};
    VkBufferImageCopy s = {.bufferOffset = sizeof areaTexBytes, .imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                           .imageExtent = {SEARCHTEX_WIDTH, SEARCHTEX_HEIGHT, 1}};
    vkCmdCopyBufferToImage(cb, buf, S.area.img, VK_IMAGE_LAYOUT_GENERAL, 1, &a);
    vkCmdCopyBufferToImage(cb, buf, S.search.img, VK_IMAGE_LAYOUT_GENERAL, 1, &s);
    all_done(cb);
    vk_defer_buffer(buf, mem);
    return S.luts_ready = 1;
}

static int work_images(VkCtx *c, VkCommandBuffer cb, uint32_t w, uint32_t h) {
    if (S.work[0].img && S.w == w && S.h == h) return 1;
    for (int i = 0; i < 3; i++) {
        if (S.work[i].view) vk_defer_view(S.work[i].view);
        if (S.work[i].img) vk_defer_image(S.work[i].img, S.work[i].mem);
        memset(&S.work[i], 0, sizeof S.work[i]);
    }
    S.w = S.h = 0;
    for (int i = 0; i < 3; i++) {
        VkImageUsageFlags u = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        if (!image(c, &S.work[i], VK_FORMAT_R8G8B8A8_UNORM, w, h, u)) return 0;
        to_general(cb, S.work[i].img, VK_IMAGE_LAYOUT_UNDEFINED);
    }
    S.w = w, S.h = h;
    return 1;
}

static void bind(VkCommandBuffer cb, int stage, VkPipeline p, const VkDescriptorImageInfo *in, uint32_t nin,
                 VkImageView out, const float metrics[4]) {
    VkWriteDescriptorSet wr[4];
    VkDescriptorImageInfo oi = {VK_NULL_HANDLE, out, VK_IMAGE_LAYOUT_GENERAL};
    for (uint32_t k = 0; k <= nin; k++)
        wr[k] = (VkWriteDescriptorSet){.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, .dstBinding = k, .descriptorCount = 1,
                                       .descriptorType = k < nin ? VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
                                                                 : VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,
                                       .pImageInfo = k < nin ? &in[k] : &oi};
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, p);
    rec_push(vk_pipeline_push_fn(), cb, VK_PIPELINE_BIND_POINT_COMPUTE, S.lay[stage], 0, nin + 1, wr);
    vkCmdPushConstants(cb, S.lay[stage], VK_SHADER_STAGE_COMPUTE_BIT, 0, 16, metrics);
    vkCmdDispatch(cb, (S.w + 7) / 8, (S.h + 7) / 8, 1);
}

static int quality(void) {
    const char *v = cfg_value("AC_ANTI_ALIASING");
    if (!v || !*v || !strcmp(v, "high") || !strcmp(v, "smaa")) return Q_HIGH;
    if (!strcmp(v, "off")) return -1;
    if (!strcmp(v, "low")) return Q_LOW;
    if (!strcmp(v, "medium")) return Q_MEDIUM;
    if (!strcmp(v, "ultra")) return Q_ULTRA;
    return Q_HIGH;
}

static void run(VkExec *ex, const VkExecTarget *t, int q) {
    VkCtx *c = vk_ctx();
    if (!S.tried) S.tried = 1, S.ok = init(c);
    if (!S.ok) return;
    VkImageView unorm = vk_exec_target_view(t->img, VK_FORMAT_R8G8B8A8_UNORM, VK_IMAGE_VIEW_TYPE_2D,
                                            VK_IMAGE_ASPECT_COLOR_BIT, t->level, t->base_layer, 1, 0);
    VkImageView srgb = vk_exec_target_view(t->img, VK_FORMAT_R8G8B8A8_SRGB, VK_IMAGE_VIEW_TYPE_2D,
                                           VK_IMAGE_ASPECT_COLOR_BIT, t->level, t->base_layer, 1, 0);
    if (!unorm || !srgb) {
        if (S.logged++ < 3) rt_log("smaa: no UNORM / sRGB view of the picture: skipped");
        return;
    }
    vk_exec_barrier(ex);   // the tonemap pass is done and visible
    VkCommandBuffer cb = ex->cb;
    if (!luts(c, cb) || !work_images(c, cb, t->width, t->height)) {
        if (S.logged++ < 3) rt_log("smaa: its images could not be made: skipped");
        return;
    }
    float m[4] = {1.0f / t->width, 1.0f / t->height, (float)t->width, (float)t->height};
    VkDescriptorImageInfo e_in[1] = {{S.linear, unorm, VK_IMAGE_LAYOUT_GENERAL}};
    bind(cb, 0, S.edges[q], e_in, 1, S.work[0].view, m);
    all_done(cb);
    VkDescriptorImageInfo w_in[3] = {{S.linear, S.work[0].view, VK_IMAGE_LAYOUT_GENERAL},
                                     {S.linear, S.area.view, VK_IMAGE_LAYOUT_GENERAL},
                                     {S.point, S.search.view, VK_IMAGE_LAYOUT_GENERAL}};
    bind(cb, 1, S.weights[q], w_in, 3, S.work[1].view, m);
    all_done(cb);
    VkDescriptorImageInfo b_in[2] = {{S.linear, srgb, VK_IMAGE_LAYOUT_GENERAL},
                                     {S.linear, S.work[1].view, VK_IMAGE_LAYOUT_GENERAL}};
    bind(cb, 2, S.blend, b_in, 2, S.work[2].view, m);
    all_done(cb);
    VkImageCopy cp = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, t->level, t->base_layer, 1},
                      .extent = {t->width, t->height, 1}};
    vkCmdCopyImage(cb, S.work[2].img, VK_IMAGE_LAYOUT_GENERAL, t->image, VK_IMAGE_LAYOUT_GENERAL, 1, &cp);
    all_done(cb);
    ex->recorded += 16;
    if (S.runs++ < 1 || S.runs % 36000 == 0)
        rt_log("smaa: %s on the %ux%u picture before the HUD (%u frames)",
               (const char *[]){"Low", "Medium", "High", "Ultra"}[q], t->width, t->height, S.runs);
}

// vk_exec_pass_begin, before the pass ex describes begins (no render pass open).
void snap_smaa_pass(VkExec *ex) {
    if (S.have_cand) {
        S.have_cand = 0;
        int q = quality();
        if (q >= 0 && S.cand_fence == ex->fence && !vk_dlaa_running()) run(ex, &S.cand, q);
    }
    const VkExecTarget *t = &ex->color[0];
    unsigned g[2];
    res_game_size(g);
    if (ex->pass_ncolor == 1 && t->image && t->img && t->format == VK_FORMAT_R8G8B8A8_SRGB && !ex->depth.image &&
        t->samples <= 1 && !t->is3d && t->width == g[0] && t->height == g[1]) {
        S.cand = *t, S.cand_fence = ex->fence, S.have_cand = 1;
    }
}
