// ULTRAWIDE-01 (AC_ASPECT=ultrawide): Snap keeps its 16:9 render targets; 16:9 perspective cameras get the window's
// ratio where their projection is built and the present stretches the picture to the window, so the 3D view is wider
// with the game's proportions. Same approach as Astral Chain's "wide" set (third_party/astral/recomp/patches-v101.txt,
// from TLin-Y's aspect-ratio pchtxt): wider lens, same targets, the interface kept in the middle 16:9.
//
// main+0x29641c, in the perspective builder (0x296400: fdiv s2,s12,s0 = cot(fov/2); 0x296418: fdiv s1,s2,s9 with
// s9 = the camera's aspect, [x20,#0x12c]): s1 is the X scale. Only a 16:9 camera is widened.
//
// What a 16:9 player would see stays the same:
// - Photos: Snap captures a photo from the tonemapped scene (a full-size RGBA8_SRGB image) by drawing it into the
//   1080x720 photo and the 360x240 thumbnail picture. In those passes the scene is replaced by its middle 1/k,
//   stretched back to full width (vkCmdBlitImage): the picture the 16:9 lens would have made.
// - Interface: the pass that draws the HUD into that same image (through a UNORM view) gets its viewport and scissor
//   narrowed to the middle 1/k, so after the present's stretch the HUD keeps its proportions, centred.
// - Frames without a widened camera (menus, the evaluation) are shown 16:9 with bars instead of stretched.
#include <math.h>
#include <string.h>
#include "cpu.h"
#include "simd.h"
#include "cfg.h"
#include "host.h"
#include "vk.h"
#include "platform/platform.h"

static volatile float snap_wide_ratio;     // the swapchain's width / height (gfx_present.c, res_wide_window)
static volatile uint64_t snap_wide_last;   // kern_now_ns of the last widened projection (game thread)

void snap_wide_window(unsigned w, unsigned h) {
    if (h) snap_wide_ratio = (float)w / (float)h;
}

static int wanted(void) { return !strcmp(cfg_value("AC_ASPECT"), "ultrawide"); }

// The widening factor: the window's ratio over 16:9, 1 when off or the window is not wider.
float snap_wide_k(void) {
    const float base = 16.0f / 9.0f, r = snap_wide_ratio;
    if (!(r > base * 1.01f && r <= 4.0f) || !wanted()) return 1.0f;
    return r / base;
}

static int widened_recently(void) {
    uint64_t t = snap_wide_last;
    return t && kern_now_ns() - t < 250000000ull;
}

// gfx_present.c gfx_fit_rect: 1 to fill the window. Ultrawide fills it only while a camera is widened.
int snap_aspect_fills(const char *aspect) {
    if (!aspect) return 0;
    if (!strcmp(aspect, "stretch")) return 1;
    return !strcmp(aspect, "ultrawide") && snap_wide_k() > 1.0f && widened_recently();
}

void snap_wide_proj_s1(Cpu *c) {
    float k = snap_wide_k();
    if (k <= 1.0f) return;
    float aspect = VSF32(9);
    if (fabsf(aspect - 16.0f / 9.0f) > 0.002f) return;
    FP_SETS(1, VSF32(1) / k);
    snap_wide_last = kern_now_ns();
}

// ---- replay thread (vk_exec.c vk_exec_pass_begin, vk_exec_draw.c)
static VkImage uw_scene;                   // the tonemapped scene of this frame (RGBA8_SRGB, full size)
static uint32_t uw_w, uw_h;
static int uw_capture, uw_hud;             // the current pass: a photo capture / the interface pass
static float uw_k = 1.0f;
static struct { VkImage img; VmaAllocation mem; VkImageView view; uint32_t w, h; } T;   // the 16:9 reconstruction

static int temp_ready(uint32_t w, uint32_t h, VkCommandBuffer cb) {
    if (T.img && T.w == w && T.h == h) return 1;
    const VkCtx *c = vk_ctx();
    if (T.img) vk_defer_view(T.view), vk_defer_image(T.img, T.mem), T.img = VK_NULL_HANDLE;
    VkImageCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                            .format = VK_FORMAT_R8G8B8A8_SRGB, .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1,
                            .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                            .usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &ci, &ai, &T.img, &T.mem, NULL) != VK_SUCCESS) return T.img = VK_NULL_HANDLE, 0;
    VkImageViewCreateInfo vi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = T.img,
                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = VK_FORMAT_R8G8B8A8_SRGB,
                                .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(c->device, &vi, NULL, &T.view) != VK_SUCCESS) {
        vmaDestroyImage(c->vma, T.img, T.mem);
        return T.img = VK_NULL_HANDLE, 0;
    }
    T.w = w, T.h = h;
    VkImageMemoryBarrier2 ib = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_NONE,
                                .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                                .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT,
                                .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                .image = T.img, .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &ib};
    vkCmdPipelineBarrier2(cb, &di);
    return 1;
}

static void mbarrier(VkCommandBuffer cb, VkPipelineStageFlags2 src, VkAccessFlags2 sa, VkPipelineStageFlags2 dst,
                     VkAccessFlags2 da) {
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2, .srcStageMask = src, .srcAccessMask = sa,
                           .dstStageMask = dst, .dstAccessMask = da};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &di);
}

static int photo_target(const VkTexImage *img) {
    if (!img || img->type != VK_IMAGE_TYPE_2D || img->format != VK_FORMAT_R8G8B8A8_UNORM) return 0;
    float s = img->scale > 0 ? img->scale : 1.0f;
    uint32_t w = (uint32_t)(img->width / s + 0.5f), h = (uint32_t)(img->height / s + 0.5f);
    return (w == 1080 && h == 720) || (w == 360 && h == 240);
}

// Outside a render pass, before it begins. 1 when the pass's viewport and scissor must be set again.
int snap_wide_pass(VkCommandBuffer cb, const VkTexImage *img, VkFormat view) {
    int was_hud = uw_hud;
    uw_capture = uw_hud = 0;
    uw_k = snap_wide_k();
    if (!img || uw_k <= 1.0f) return was_hud;
    if (img->format == VK_FORMAT_R8G8B8A8_SRGB && view == VK_FORMAT_R8G8B8A8_SRGB && img->type == VK_IMAGE_TYPE_2D &&
        img->width >= 640 && img->width * 9 == img->height * 16) {
        uw_scene = img->image, uw_w = img->width, uw_h = img->height;
        return was_hud;
    }
    if (uw_scene && img->image == uw_scene && view == VK_FORMAT_R8G8B8A8_UNORM) {
        uw_hud = widened_recently();
        return uw_hud != was_hud || uw_hud;
    }
    if (uw_scene && photo_target(img) && temp_ready(uw_w, uw_h, cb)) {
        int32_t half = (int32_t)(uw_w / (2.0f * uw_k) + 0.5f), cx = (int32_t)uw_w / 2;
        VkImageBlit b = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                         .srcOffsets = {{cx - half, 0, 0}, {cx + half, (int32_t)uw_h, 1}},
                         .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                         .dstOffsets = {{0, 0, 0}, {(int32_t)uw_w, (int32_t)uw_h, 1}}};
        mbarrier(cb, VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, VK_ACCESS_2_MEMORY_WRITE_BIT, VK_PIPELINE_STAGE_2_BLIT_BIT,
                 VK_ACCESS_2_TRANSFER_READ_BIT | VK_ACCESS_2_TRANSFER_WRITE_BIT);
        vkCmdBlitImage(cb, uw_scene, VK_IMAGE_LAYOUT_GENERAL, T.img, VK_IMAGE_LAYOUT_GENERAL, 1, &b, VK_FILTER_LINEAR);
        mbarrier(cb, VK_PIPELINE_STAGE_2_BLIT_BIT, VK_ACCESS_2_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                 VK_ACCESS_2_MEMORY_READ_BIT);
        uw_capture = 1;
        static int logged;
        if (!logged++) rt_log("ultrawide: photos are taken from the 16:9 view (middle %.0f%% of the wide scene)", 100.0f / uw_k);
    }
    return was_hud;
}

int snap_wide_capture(void) { return uw_capture; }

// A capture pass samples the reconstructed 16:9 scene instead of the wide one.
VkImageView snap_wide_capture_view(VkImage image, VkImageView fallback) {
    return uw_capture && image == uw_scene && T.view ? T.view : fallback;
}

void snap_wide_viewport(uint32_t pass_w, VkViewport *v) {
    if (!uw_hud) return;
    float cx = pass_w * 0.5f;
    v->x = cx + (v->x - cx) / uw_k;
    v->width /= uw_k;
}

void snap_wide_scissor(uint32_t pass_w, VkRect2D *r) {
    if (!uw_hud) return;
    float cx = pass_w * 0.5f, x0 = cx + (r->offset.x - cx) / uw_k, x1 = cx + (r->offset.x + (float)r->extent.width - cx) / uw_k;
    r->offset.x = (int32_t)floorf(x0);
    r->extent.width = (uint32_t)ceilf(x1 - floorf(x0));
}
