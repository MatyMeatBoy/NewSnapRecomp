// SS-03 (AC_HD_PHOTOS, on by default): photo thumbnails shown from a full-resolution copy.
//
// When a photo is taken Snap renders the pre-HUD 1920x1080 scene into a 360x240 RGBA8 image, then encodes that into
// a 360x240 BC1 texture (a draw through the BC texture's blocks: a block view, or vk_exec.c's stand-in on AMD's RDNA
// 1/2 driver). The in-level preview, the folder screen and the photo-selection screen draw that BC1 texture, enlarged,
// so they show a 360x240 picture. Here the 360x240 RGBA8 image is drawn 3x larger (1080x720, snap_output_scale.h
// snap_hd_photo_scale; the encoder still reads it at its own size), and when the next pass encodes a 360x240 BC
// texture, that 1080x720 picture is copied to an image of ours kept for the BC texture. Draws that sample the BC
// texture get the copy instead (vk_exec_draw.c tex_info_full). Same picture, same UV space, any GPU.
//
// Kept honest: a BC thumbnail that the game writes in any other way (a CPU upload, a pass not preceded by a fresh
// 360x240 picture) drops its copy and shows the game's own texture again; the copy goes with the texture
// (vk_exec_image_gone). Saved photos, thumbnails and the evaluation never read these copies.
#include <string.h>
#include "cfg.h"
#include "host.h"
#include "vk.h"
#include "platform/platform.h"

#define HD_MAX 96

typedef struct { VkImage bc, img; VmaAllocation alloc; VkImageView view; uint32_t w, h; } HdPhoto;
static HdPhoto hd[HD_MAX];
static int nhd;
static PlatMutex hd_lock = PLAT_MUTEX_INIT;
static volatile uint32_t hd_gen;
static VkImage last_src;              // the 360x240 picture drawn larger, waiting for its encode (replay thread)
static uint32_t last_w, last_h;

int snap_hd_photo_on(void) {
    static int on = -1;
    if (on < 0) {
        const char *v = cfg_get("AC_HD_PHOTOS");
        on = !(v && !strcmp(v, "0"));
        rt_log("snap: HD photo thumbnails %s (AC_HD_PHOTOS)", on ? "on" : "off");
    }
    return on;
}

uint32_t snap_hd_photo_gen(void) { return __atomic_load_n(&hd_gen, __ATOMIC_RELAXED); }

static int is_bc_thumb(const VkTexImage *img) {
    return img && img->type == VK_IMAGE_TYPE_2D && img->width == 360 && img->height == 240 &&
           (img->format == VK_FORMAT_BC1_RGBA_UNORM_BLOCK || img->format == VK_FORMAT_BC1_RGB_UNORM_BLOCK ||
            img->format == VK_FORMAT_BC3_UNORM_BLOCK);
}

static int is_picture(const VkTexImage *img) {
    return img && img->type == VK_IMAGE_TYPE_2D && img->format == VK_FORMAT_R8G8B8A8_UNORM && img->scale > 1.0f &&
           img->width == (uint32_t)(360 * img->scale + 0.5f) && img->height == (uint32_t)(240 * img->scale + 0.5f);
}

static void drop_locked(int i) {
    vk_defer_view(hd[i].view);
    vk_defer_image(hd[i].img, hd[i].alloc);
    hd[i] = hd[--nhd];
    __atomic_add_fetch(&hd_gen, 1, __ATOMIC_RELAXED);
}

void snap_hd_photo_gone(VkImage bc) {
    plat_mutex_lock(&hd_lock);
    for (int i = 0; i < nhd; i++)
        if (hd[i].bc == bc) drop_locked(i--);
    plat_mutex_unlock(&hd_lock);
}

VkImageView snap_hd_photo_view(VkImage bc, VkImageView fallback) {
    if (!nhd) return fallback;
    VkImageView v = fallback;
    plat_mutex_lock(&hd_lock);
    for (int i = 0; i < nhd; i++)
        if (hd[i].bc == bc) { v = hd[i].view; break; }
    plat_mutex_unlock(&hd_lock);
    return v;
}

static void barrier(VkCommandBuffer cb, VkPipelineStageFlags2 src, VkAccessFlags2 sa, VkPipelineStageFlags2 dst,
                    VkAccessFlags2 da) {
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2, .srcStageMask = src, .srcAccessMask = sa,
                           .dstStageMask = dst, .dstAccessMask = da};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &di);
}

static int make(HdPhoto *p, VkImage bc, uint32_t w, uint32_t h, VkCommandBuffer cb) {
    VkImageCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                            .format = VK_FORMAT_R8G8B8A8_UNORM, .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1,
                            .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                            .usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    *p = (HdPhoto){.bc = bc, .w = w, .h = h};
    if (vmaCreateImage(vk_ctx()->vma, &ci, &ai, &p->img, &p->alloc, NULL) != VK_SUCCESS) return 0;
    VkImageViewCreateInfo vi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = p->img,
                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = VK_FORMAT_R8G8B8A8_UNORM,
                                .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    if (vkCreateImageView(vk_ctx()->device, &vi, NULL, &p->view) != VK_SUCCESS) {
        vmaDestroyImage(vk_ctx()->vma, p->img, p->alloc);
        return 0;
    }
    VkImageMemoryBarrier2 ib = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_NONE,
                                .dstStageMask = VK_PIPELINE_STAGE_2_COPY_BIT, .dstAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT,
                                .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                .image = p->img, .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &ib};
    vkCmdPipelineBarrier2(cb, &di);
    return 1;
}

// vk_exec.c vk_exec_pass_begin, outside a render pass, for the pass's first colour target.
void snap_hd_photo_pass(VkCommandBuffer cb, const VkTexImage *img) {
    if (!img || !snap_hd_photo_on()) return;
    if (is_picture(img)) {
        last_src = img->image, last_w = img->width, last_h = img->height;
        return;
    }
    if (!is_bc_thumb(img)) return;
    VkImage src = last_src;
    last_src = VK_NULL_HANDLE;
    plat_mutex_lock(&hd_lock);
    int at = -1;
    for (int i = 0; i < nhd; i++)
        if (hd[i].bc == img->image) at = i;
    if (!src) {   // the BC texture is drawn without a fresh picture: show the game's own from now on
        if (at >= 0) drop_locked(at);
        plat_mutex_unlock(&hd_lock);
        return;
    }
    if (at >= 0 && (hd[at].w != last_w || hd[at].h != last_h)) drop_locked(at), at = -1;
    if (at < 0) {
        static int warned;
        if (nhd == HD_MAX) drop_locked(0);   // the oldest thumbnail falls back to the game's texture
        if (!make(&hd[nhd], img->image, last_w, last_h, cb)) {
            if (!warned++) rt_log("snap: HD photo thumbnail image could not be made: the game's thumbnail stays");
            plat_mutex_unlock(&hd_lock);
            return;
        }
        at = nhd++;
        static int logged;
        if (!logged++) rt_log("snap: HD photo thumbnails from the %ux%u picture (first at BC texture %ux%u)", last_w,
                              last_h, img->width, img->height);
    }
    barrier(cb, VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, VK_ACCESS_2_MEMORY_WRITE_BIT, VK_PIPELINE_STAGE_2_COPY_BIT,
            VK_ACCESS_2_TRANSFER_READ_BIT | VK_ACCESS_2_TRANSFER_WRITE_BIT);
    VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .extent = {last_w, last_h, 1}};
    vkCmdCopyImage(cb, src, VK_IMAGE_LAYOUT_GENERAL, hd[at].img, VK_IMAGE_LAYOUT_GENERAL, 1, &rg);
    barrier(cb, VK_PIPELINE_STAGE_2_COPY_BIT, VK_ACCESS_2_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
            VK_ACCESS_2_MEMORY_READ_BIT);
    __atomic_add_fetch(&hd_gen, 1, __ATOMIC_RELAXED);
    plat_mutex_unlock(&hd_lock);
}
