// TEXPACK-01: HD texture packs by content hash, the way Dolphin's custom textures work (dump by hash, load by hash).
//
// Snap's textures live in Oodle-compressed, encrypted .drp archives; replacing them there means rebuilding archives.
// Here the game keeps its own files and textures: when the runtime uploads a texture the game wrote (vk_texture.c
// upload), its storage bytes are hashed. NEWSNAP_TEX_DUMP=<folder> writes each new 2D colour texture's level 0 there as
// <hash>.png (a GPU blit decompresses BC/ASTC stand-ins to RGBA8). The pack is a folder of <hash>.dds files next to
// newsnap.exe (texpack/, AC_TEX_PACK=0 turns it off): BC7, BC1, BC3 or RGBA8 with any size and mip count. A texture
// whose hash has a file gets that image, and its sampled views (vk_exec_draw.c get_view) are made on it with the same
// channel mapping as the game's view, so any size works with the game's normalized coordinates. Same on every GPU.
// tools/texpack.py builds a pack from a dump (Real-ESRGAN, BC7). A pack holds game-derived pictures: it is made
// locally from the player's own game and never distributed.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cfg.h"
#include "host.h"
#include "vk.h"
#include "platform/platform.h"

typedef struct { VkImage game, img; VmaAllocation mem; VkFormat fmt; uint32_t w, h, levels; uint64_t hash; } HdTex;
#define HD_MAX 4096
static HdTex hd[HD_MAX];
static int nhd;
static PlatMutex lock = PLAT_MUTEX_INIT;
static volatile uint32_t gen;
static uint64_t *index_;   // sorted hashes of the pack's files
static int nindex = -1;
static char pack_dir[1024], dump_dir[1024];

uint32_t snap_texpack_gen(void) { return __atomic_load_n(&gen, __ATOMIC_RELAXED); }

static uint64_t hash_bytes(const uint8_t *p, uint64_t n, uint64_t seed) {
    uint64_t h = 0x9E3779B97F4A7C15ull ^ seed ^ (n * 0xC2B2AE3D27D4EB4Full);
    uint64_t i = 0;
    for (; i + 8 <= n; i += 8) {
        uint64_t w;
        memcpy(&w, p + i, 8);
        h = (h ^ w) * 0x9E3779B97F4A7C15ull;
        h ^= h >> 29;
    }
    for (; i < n; i++) h = (h ^ p[i]) * 0x100000001B3ull;
    h ^= h >> 32;
    return h * 0xD6E8FEB86659FD93ull ^ (h >> 31);
}

static int cmp_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x < y ? -1 : x > y;
}

typedef struct { uint64_t *list; int n, cap; } Names;
static int list_cb(const char *name, int kind, uint64_t size, void *ctx) {
    (void)size;
    Names *l = ctx;
    if (kind != PLAT_FS_FILE || strlen(name) != 20 || strcmp(name + 16, ".dds")) return 1;
    char *end;
    uint64_t v = strtoull(name, &end, 16);
    if (end != name + 16) return 1;
    if (l->n == l->cap) {
        l->cap = l->cap ? l->cap * 2 : 256;
        l->list = realloc(l->list, sizeof *l->list * (size_t)l->cap);
        if (!l->list) rt_fatal("texpack: out of memory");
    }
    l->list[l->n++] = v;
    return 1;
}

static void setup(void) {
    if (nindex >= 0) return;
    nindex = 0;
    const char *d = getenv("NEWSNAP_TEX_DUMP");
    if (d && *d) {
        snprintf(dump_dir, sizeof dump_dir, "%s", d);
        plat_fs_mkdir(dump_dir);
        rt_log("texpack: dumping new textures to %s", dump_dir);
    }
    const char *on = cfg_get("AC_TEX_PACK");
    if (on && !strcmp(on, "0")) return;
    char exe[900];
    if (!plat_exe_path(exe, sizeof exe)) return;
    char *slash = strrchr(exe, '/'), *bs = strrchr(exe, 92);   // 92: backslash
    if (bs && (!slash || bs > slash)) slash = bs;
    if (slash) *slash = 0;
    snprintf(pack_dir, sizeof pack_dir, "%s/texpack", exe);
    Names l = {0};
    plat_fs_list(pack_dir, list_cb, &l);
    if (!l.n) return;
    qsort(l.list, (size_t)l.n, sizeof *l.list, cmp_u64);
    index_ = l.list, nindex = l.n;
    rt_log("texpack: %d HD textures in %s", nindex, pack_dir);
}

static int in_pack(uint64_t h) {
    return nindex > 0 && bsearch(&h, index_, (size_t)nindex, sizeof h, cmp_u64);
}

static int is_srgb(VkFormat f) {
    return f == VK_FORMAT_R8G8B8A8_SRGB || f == VK_FORMAT_B8G8R8A8_SRGB || f == VK_FORMAT_BC1_RGBA_SRGB_BLOCK ||
           f == VK_FORMAT_BC1_RGB_SRGB_BLOCK || f == VK_FORMAT_BC2_SRGB_BLOCK || f == VK_FORMAT_BC3_SRGB_BLOCK ||
           f == VK_FORMAT_BC7_SRGB_BLOCK || (f >= VK_FORMAT_ASTC_4x4_SRGB_BLOCK && f <= VK_FORMAT_ASTC_12x12_SRGB_BLOCK &&
                                             (f - VK_FORMAT_ASTC_4x4_SRGB_BLOCK) % 2 == 0);
}

static int eligible(const VkTexImage *img) {
    return img && img->type == VK_IMAGE_TYPE_2D && img->layers == 1 && img->samples == 1 &&
           img->aspect == VK_IMAGE_ASPECT_COLOR_BIT && img->width >= 32 && img->height >= 32 && !img->skip;
}

// ---- dump: level 0 through a blit to RGBA8, read back after the upload batch, written as PNG
static void dump(const VkTexImage *img, uint64_t h) {
    char path[1200];
    snprintf(path, sizeof path, "%s/%016llx.png", dump_dir, (unsigned long long)h);
    FILE *f = fopen(path, "rb");
    if (f) { fclose(f); return; }
    VkFormatProperties fp;
    vkGetPhysicalDeviceFormatProperties(vk_ctx()->phys, img->format, &fp);
    if (!(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT)) return;
    const VkCtx *c = vk_ctx();
    VkFormat tf = is_srgb(img->format) ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    uint32_t w = img->width, h2 = img->height;
    VkImage tmp;
    VmaAllocation tmem;
    VkImageCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D, .format = tf,
                            .extent = {w, h2, 1}, .mipLevels = 1, .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT,
                            .tiling = VK_IMAGE_TILING_OPTIMAL,
                            .usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &ci, &ai, &tmp, &tmem, NULL) != VK_SUCCESS) return;
    VkBuffer rb;
    VmaAllocation ra;
    uint8_t *map = vk_staging((VkDeviceSize)w * h2 * 4, &rb, &ra);
    VkCommandBuffer cb = vk_upload_begin();
    VkImageMemoryBarrier2 ib = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
                                .srcStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, .srcAccessMask = VK_ACCESS_2_MEMORY_WRITE_BIT,
                                .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                                .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT,
                                .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                .image = tmp, .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &ib};
    vkCmdPipelineBarrier2(cb, &di);
    VkImageBlit b = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .srcOffsets = {{0, 0, 0}, {(int32_t)w, (int32_t)h2, 1}},
                     .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .dstOffsets = {{0, 0, 0}, {(int32_t)w, (int32_t)h2, 1}}};
    vkCmdBlitImage(cb, img->image, VK_IMAGE_LAYOUT_GENERAL, tmp, VK_IMAGE_LAYOUT_GENERAL, 1, &b, VK_FILTER_NEAREST);
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_BLIT_BIT,
                           .srcAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT, .dstStageMask = VK_PIPELINE_STAGE_2_COPY_BIT,
                           .dstAccessMask = VK_ACCESS_2_TRANSFER_READ_BIT};
    VkDependencyInfo dm = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &dm);
    VkBufferImageCopy rg = {.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .imageExtent = {w, h2, 1}};
    vkCmdCopyImageToBuffer(cb, tmp, VK_IMAGE_LAYOUT_GENERAL, rb, 1, &rg);
    vk_upload_end();
    vk_upload_flush(1);
    vmaInvalidateAllocation(c->vma, ra, 0, VK_WHOLE_SIZE);
    rt_write_png(path, map, w, h2);
    vmaDestroyBuffer(c->vma, rb, ra);
    vmaDestroyImage(c->vma, tmp, tmem);
    static int n;
    if (n++ < 3 || n % 500 == 0) rt_log("texpack: dumped %d textures (last %016llx, %ux%u, vk format %d)", n,
                                        (unsigned long long)h, w, h2, (int)img->format);
}

// ---- load: <hash>.dds, DX10 header or legacy DXT1/DXT5
static VkFormat dds_format(uint32_t dxgi, int srgb) {
    switch (dxgi) {
    case 98: case 99: return srgb ? VK_FORMAT_BC7_SRGB_BLOCK : VK_FORMAT_BC7_UNORM_BLOCK;
    case 71: case 72: return srgb ? VK_FORMAT_BC1_RGBA_SRGB_BLOCK : VK_FORMAT_BC1_RGBA_UNORM_BLOCK;
    case 77: case 78: return srgb ? VK_FORMAT_BC3_SRGB_BLOCK : VK_FORMAT_BC3_UNORM_BLOCK;
    case 28: case 29: return srgb ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    default: return VK_FORMAT_UNDEFINED;
    }
}

static uint64_t level_bytes(VkFormat f, uint32_t w, uint32_t h) {
    if (f == VK_FORMAT_R8G8B8A8_SRGB || f == VK_FORMAT_R8G8B8A8_UNORM) return (uint64_t)w * h * 4;
    uint64_t blocks = (uint64_t)((w + 3) / 4) * ((h + 3) / 4);
    return blocks * (f == VK_FORMAT_BC1_RGBA_UNORM_BLOCK || f == VK_FORMAT_BC1_RGBA_SRGB_BLOCK ? 8 : 16);
}

static int load(const VkTexImage *img, uint64_t hsh, HdTex *out) {
    char path[1200];
    snprintf(path, sizeof path, "%s/%016llx.dds", pack_dir, (unsigned long long)hsh);
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    uint8_t hd_[148];
    size_t got = fread(hd_, 1, sizeof hd_, f);
    uint32_t magic, height, width, mips, fourcc, dxgi = 0;
    memcpy(&magic, hd_, 4), memcpy(&height, hd_ + 12, 4), memcpy(&width, hd_ + 16, 4), memcpy(&mips, hd_ + 28, 4);
    memcpy(&fourcc, hd_ + 84, 4);
    long data = 128;
    if (got < 128 || magic != 0x20534444) { fclose(f); return 0; }
    if (fourcc == 0x30315844 && got >= 148) memcpy(&dxgi, hd_ + 128, 4), data = 148;   // "DX10"
    else if (fourcc == 0x31545844) dxgi = 71;   // "DXT1"
    else if (fourcc == 0x35545844) dxgi = 77;   // "DXT5"
    VkFormat fmt = dds_format(dxgi, is_srgb(img->format));
    if (!fmt || !width || !height || width > 16384 || height > 16384) { fclose(f); return 0; }
    if (!mips) mips = 1;
    uint64_t total = 0;
    for (uint32_t l = 0; l < mips; l++) total += level_bytes(fmt, width >> l ? width >> l : 1, height >> l ? height >> l : 1);
    const VkCtx *c = vk_ctx();
    VkImageCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D, .format = fmt,
                            .extent = {width, height, 1}, .mipLevels = mips, .arrayLayers = 1,
                            .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                            .usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    *out = (HdTex){.game = img->image, .fmt = fmt, .w = width, .h = height, .levels = mips, .hash = hsh};
    if (vmaCreateImage(c->vma, &ci, &ai, &out->img, &out->mem, NULL) != VK_SUCCESS) { fclose(f); return 0; }
    VkBuffer sb;
    uint8_t *stg = vk_staging(total, &sb, NULL);
    fseek(f, data, SEEK_SET);
    size_t rd = fread(stg, 1, (size_t)total, f);
    fclose(f);
    if (rd != total) {
        vmaDestroyImage(c->vma, out->img, out->mem);
        return 0;
    }
    VkCommandBuffer cb = vk_upload_begin();
    VkImageMemoryBarrier2 ib = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_NONE,
                                .dstStageMask = VK_PIPELINE_STAGE_2_COPY_BIT, .dstAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT,
                                .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                .image = out->img, .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, mips, 0, 1}};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &ib};
    vkCmdPipelineBarrier2(cb, &di);
    VkBufferImageCopy rg[16];
    uint64_t off = 0;
    uint32_t n = mips < 16 ? mips : 16;
    for (uint32_t l = 0; l < n; l++) {
        uint32_t lw = width >> l ? width >> l : 1, lh = height >> l ? height >> l : 1;
        rg[l] = (VkBufferImageCopy){.bufferOffset = off, .imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, l, 0, 1},
                                    .imageExtent = {lw, lh, 1}};
        off += level_bytes(fmt, lw, lh);
    }
    vkCmdCopyBufferToImage(cb, sb, out->img, VK_IMAGE_LAYOUT_GENERAL, n, rg);
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2, .srcStageMask = VK_PIPELINE_STAGE_2_COPY_BIT,
                           .srcAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT, .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                           .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT};
    VkDependencyInfo dm = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &dm);
    vk_upload_end();
    out->levels = n;
    return 1;
}

void vk_exec_image_gone(VkImage image);
static void drop_locked(int i) {
    vk_exec_image_gone(hd[i].img);   // its views (get_view keeps them under the HD image)
    vk_defer_image(hd[i].img, hd[i].mem);
    hd[i] = hd[--nhd];
    __atomic_add_fetch(&gen, 1, __ATOMIC_RELAXED);
}

// vk_texture.c upload, after the game's content went to img: hash it, dump it, attach or drop its HD image.
void snap_texpack_uploaded(const VkTexImage *img, const void *mem, uint64_t size, int nvn_format) {
    setup();
    if (!eligible(img) || !mem || !size || (!dump_dir[0] && nindex <= 0 && !nhd)) return;
    uint64_t h = hash_bytes(mem, size, (uint64_t)img->width << 32 ^ (uint64_t)img->height << 16 ^ (uint64_t)(uint32_t)nvn_format);
    if (dump_dir[0]) dump(img, h);
    plat_mutex_lock(&lock);
    int at = -1;
    for (int i = 0; i < nhd; i++)
        if (hd[i].game == img->image) at = i;
    if (at >= 0 && hd[at].hash == h) { plat_mutex_unlock(&lock); return; }
    if (at >= 0) drop_locked(at);
    if (in_pack(h) && nhd < HD_MAX) {
        HdTex t;
        if (load(img, h, &t)) {
            hd[nhd++] = t;
            __atomic_add_fetch(&gen, 1, __ATOMIC_RELAXED);
            static int n;
            if (n++ < 3 || n % 200 == 0) rt_log("texpack: %d HD textures in use (last %016llx, %ux%u -> %ux%u)", n,
                                                (unsigned long long)h, img->width, img->height, t.w, t.h);
        }
    }
    plat_mutex_unlock(&lock);
}

void snap_texpack_gone(VkImage game) {
    if (!nhd) return;
    plat_mutex_lock(&lock);
    for (int i = 0; i < nhd; i++)
        if (hd[i].game == game) drop_locked(i--);
    plat_mutex_unlock(&lock);
}

// vk_exec_draw.c get_view: the HD image of img and its format, or VK_NULL_HANDLE. The caller makes the view with the
// game view's channel mapping over all of the HD image's levels.
VkImage snap_texpack_image(VkImage game, VkFormat *fmt, uint32_t *levels) {
    if (!nhd) return VK_NULL_HANDLE;
    VkImage r = VK_NULL_HANDLE;
    plat_mutex_lock(&lock);
    for (int i = 0; i < nhd; i++)
        if (hd[i].game == game) { r = hd[i].img, *fmt = hd[i].fmt, *levels = hd[i].levels; break; }
    plat_mutex_unlock(&lock);
    return r;
}
