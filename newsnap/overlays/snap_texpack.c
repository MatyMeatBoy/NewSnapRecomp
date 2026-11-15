// TEXPACK-01: HD texture packs by content hash, the way Dolphin's custom textures work (dump by hash, load by hash).
//
// Snap's textures live in Oodle-compressed, encrypted .drp archives; replacing them there means rebuilding archives.
// Here the game keeps its own files and textures: when the runtime uploads a texture the game wrote (vk_texture.c
// upload), its storage bytes are hashed. NEWSNAP_TEX_DUMP=<folder> writes each new 2D colour texture's level 0 there as
// <hash>.png (a GPU blit decompresses BC/ASTC stand-ins to RGBA8). The pack is a folder of <hash>.dds files next to
// newsnap.exe (texpack/, AC_TEX_PACK=0 turns it off): BC7, BC1, BC3 or RGBA8 with any size and mip count. A texture
// whose hash has a file gets that image, and its sampled views (vk_exec_draw.c get_view) are made on it with the same
// channel mapping as the game's view, so any size works with the game's normalized coordinates. Same on every GPU.
// AC_TEX_PACK_SAVE=1 saves them to texpack/src; newsnap/texpack_gen.py (the launcher's «Generar pack de texturas HD»)
// builds the pack from there (Real-ESRGAN, BC1/BC3). A pack holds game-derived pictures: it is made
// locally from the player's own game and never distributed.
//
// HD-SHADOW-01 (AC_HD_SHADOWS=1, off by default): the shadows of scenery and plants are baked into the levels' light
// maps, single-level BC6H textures of 512x512 texels or less, so the shadow map scale does not reach them. With the
// option on, each new light map is written once, as float (RGBA16F DDS), to hdshadows/src/<hash>.dds; the launcher's
// tools/hdshadows.py enlarges them (Real-ESRGAN on a log encoding, light kept, no seams at the UV islands) into
// hdshadows/<hash>.dds (BC6H with mips), which replace them by hash the next time they load.
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
static uint64_t *light_index;   // HD-SHADOW-01: hdshadows/<hash>.dds
static int nlight, light_on;
static char light_dir[1024], light_src[1100];

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
    char exe[900];
    if (!plat_exe_path(exe, sizeof exe)) return;
    char *slash = strrchr(exe, '/'), *bs = strrchr(exe, 92);   // 92: backslash
    if (bs && (!slash || bs > slash)) slash = bs;
    if (slash) *slash = 0;
    const char *shadows = cfg_get("AC_HD_SHADOWS");
    const char *save = cfg_get("AC_TEX_PACK_SAVE");   // TEXPACK-01: the launcher's pack generation reads texpack/src
    if (!dump_dir[0] && save && !strcmp(save, "1")) {
        char packs[1000];
        snprintf(packs, sizeof packs, "%s/texpack", exe);
        plat_fs_mkdir(packs);
        snprintf(dump_dir, sizeof dump_dir, "%s/src", packs);
        plat_fs_mkdir(dump_dir);
        rt_log("texpack: saving new textures for the pack to %s", dump_dir);
    }
    if (shadows && !strcmp(shadows, "1")) {
        light_on = 1;
        snprintf(light_dir, sizeof light_dir, "%s/hdshadows", exe);
        snprintf(light_src, sizeof light_src, "%s/src", light_dir);
        plat_fs_mkdir(light_dir), plat_fs_mkdir(light_src);
        Names l = {0};
        plat_fs_list(light_dir, list_cb, &l);
        if (l.n) qsort(l.list, (size_t)l.n, sizeof *l.list, cmp_u64);
        light_index = l.list, nlight = l.n;
        rt_log("texpack: HD shadows on, %d HD light maps in %s", nlight, light_dir);
    }
    const char *on = cfg_get("AC_TEX_PACK");
    if (on && !strcmp(on, "0")) return;
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

static int in_light(uint64_t h) {
    return nlight > 0 && bsearch(&h, light_index, (size_t)nlight, sizeof h, cmp_u64);
}

// A level's light map: a single-level 2D BC6H texture (HD-SHADOW-01).
static int is_light_map(const VkTexImage *img) {
    return img && (img->format == VK_FORMAT_BC6H_UFLOAT_BLOCK || img->format == VK_FORMAT_BC6H_SFLOAT_BLOCK) &&
           img->type == VK_IMAGE_TYPE_2D && img->layers == 1 && img->samples == 1 &&
           img->width >= 64 && img->height >= 64 && img->width <= 2048 && img->height <= 2048 && !img->skip;
}

static int is_srgb(VkFormat f) {
    return f == VK_FORMAT_R8G8B8A8_SRGB || f == VK_FORMAT_B8G8R8A8_SRGB || f == VK_FORMAT_BC1_RGBA_SRGB_BLOCK ||
           f == VK_FORMAT_BC1_RGB_SRGB_BLOCK || f == VK_FORMAT_BC2_SRGB_BLOCK || f == VK_FORMAT_BC3_SRGB_BLOCK ||
           f == VK_FORMAT_BC7_SRGB_BLOCK || (f >= VK_FORMAT_ASTC_4x4_SRGB_BLOCK && f <= VK_FORMAT_ASTC_12x12_SRGB_BLOCK &&
                                             (f - VK_FORMAT_ASTC_4x4_SRGB_BLOCK) % 2 == 0);
}

// Colour textures only: the game stores them as sRGB (BC1/BC3/BC7 sRGB, ASTC decoded to RGBA8 sRGB). Normal maps (BC5),
// masks (BC4) and HDR maps (BC6H) are data, not pictures: an upscaler would invent values in them.
static int eligible(const VkTexImage *img) {
    return img && is_srgb(img->format) && img->type == VK_IMAGE_TYPE_2D && img->layers == 1 && img->samples == 1 &&
           img->aspect == VK_IMAGE_ASPECT_COLOR_BIT && img->width >= 32 && img->height >= 32 && !img->skip;
}

// NEWSNAP_TEX_DUMP_ALL=1 (diagnostics, HD-SHADOW-01): the dump also takes the data textures (BC6H lighting, BC4/BC5,
// unorm BC3), clamped to 0..1 through the RGBA8 blit, named <hash>-f<vk format>.png; they never enter a pack.
static int dump_all(void) {
    static int on = -1;
    if (on < 0) { const char *v = getenv("NEWSNAP_TEX_DUMP_ALL"); on = v && !strcmp(v, "1"); }
    return on;
}

static int eligible_data(const VkTexImage *img) {
    return img && !is_srgb(img->format) && img->type == VK_IMAGE_TYPE_2D && img->layers == 1 && img->samples == 1 &&
           img->aspect == VK_IMAGE_ASPECT_COLOR_BIT && img->width >= 32 && img->height >= 32 && !img->skip;
}

static void write_dds_rgba16f(const char *path, const void *px, uint32_t w, uint32_t h) {
    uint8_t hdr[148] = {0};
    uint32_t v;
    memcpy(hdr, "DDS ", 4);
    v = 124, memcpy(hdr + 4, &v, 4);
    v = 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, memcpy(hdr + 8, &v, 4);
    memcpy(hdr + 12, &h, 4), memcpy(hdr + 16, &w, 4);
    v = w * 8, memcpy(hdr + 20, &v, 4);
    v = 1, memcpy(hdr + 28, &v, 4);
    v = 32, memcpy(hdr + 76, &v, 4);
    v = 0x4, memcpy(hdr + 80, &v, 4);
    memcpy(hdr + 84, "DX10", 4);
    v = 0x1000, memcpy(hdr + 108, &v, 4);
    v = 10, memcpy(hdr + 128, &v, 4);   // DXGI_FORMAT_R16G16B16A16_FLOAT
    v = 3, memcpy(hdr + 132, &v, 4);    // TEXTURE2D
    v = 1, memcpy(hdr + 140, &v, 4);    // array size
    char tmp[1210];
    snprintf(tmp, sizeof tmp, "%s.part", path);
    FILE *f = fopen(tmp, "wb");
    if (!f) return;
    int ok = fwrite(hdr, 1, sizeof hdr, f) == sizeof hdr && fwrite(px, 8, (size_t)w * h, f) == (size_t)w * h;
    fclose(f);
    if (ok) rename(tmp, path);
    else remove(tmp);
}

// ---- dump: level 0 through a blit to RGBA8 (PNG) or, for a light map, RGBA16F (DDS), read back after the upload
static void dump_to(const VkTexImage *img, uint64_t h, const char *dir, int light) {
    char path[1200];
    if (light) snprintf(path, sizeof path, "%s/%016llx.dds", dir, (unsigned long long)h);
    else if (is_srgb(img->format)) snprintf(path, sizeof path, "%s/%016llx.png", dir, (unsigned long long)h);
    else snprintf(path, sizeof path, "%s/%016llx-f%d.png", dir, (unsigned long long)h, (int)img->format);
    FILE *f = fopen(path, "rb");
    if (f) { fclose(f); return; }
    VkFormatProperties fp;
    vkGetPhysicalDeviceFormatProperties(vk_ctx()->phys, img->format, &fp);
    if (!(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT)) return;
    const VkCtx *c = vk_ctx();
    VkFormat tf = light ? VK_FORMAT_R16G16B16A16_SFLOAT : is_srgb(img->format) ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    uint32_t bpp = light ? 8 : 4;
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
    uint8_t *map = vk_staging((VkDeviceSize)w * h2 * bpp, &rb, &ra);
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
    if (light) write_dds_rgba16f(path, map, w, h2);
    else rt_write_png(path, map, w, h2);
    vmaDestroyBuffer(c->vma, rb, ra);
    vmaDestroyImage(c->vma, tmp, tmem);
    static int n;
    if (n++ < 3 || n % 500 == 0) rt_log("texpack: dumped %d textures (last %016llx, %ux%u, vk format %d)", n,
                                        (unsigned long long)h, w, h2, (int)img->format);
}

static void dump(const VkTexImage *img, uint64_t h) { dump_to(img, h, dump_dir, 0); }

// ---- load: <hash>.dds, DX10 header or legacy DXT1/DXT5
static VkFormat dds_format(uint32_t dxgi, int srgb) {
    switch (dxgi) {
    case 98: case 99: return srgb ? VK_FORMAT_BC7_SRGB_BLOCK : VK_FORMAT_BC7_UNORM_BLOCK;
    case 71: case 72: return srgb ? VK_FORMAT_BC1_RGBA_SRGB_BLOCK : VK_FORMAT_BC1_RGBA_UNORM_BLOCK;
    case 77: case 78: return srgb ? VK_FORMAT_BC3_SRGB_BLOCK : VK_FORMAT_BC3_UNORM_BLOCK;
    case 28: case 29: return srgb ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    case 95: return VK_FORMAT_BC6H_UFLOAT_BLOCK;
    case 96: return VK_FORMAT_BC6H_SFLOAT_BLOCK;
    case 10: return VK_FORMAT_R16G16B16A16_SFLOAT;
    default: return VK_FORMAT_UNDEFINED;
    }
}

static uint64_t level_bytes(VkFormat f, uint32_t w, uint32_t h) {
    if (f == VK_FORMAT_R8G8B8A8_SRGB || f == VK_FORMAT_R8G8B8A8_UNORM) return (uint64_t)w * h * 4;
    if (f == VK_FORMAT_R16G16B16A16_SFLOAT) return (uint64_t)w * h * 8;
    uint64_t blocks = (uint64_t)((w + 3) / 4) * ((h + 3) / 4);
    return blocks * (f == VK_FORMAT_BC1_RGBA_UNORM_BLOCK || f == VK_FORMAT_BC1_RGBA_SRGB_BLOCK ? 8 : 16);
}

static int load(const VkTexImage *img, uint64_t hsh, HdTex *out, const char *dir) {
    char path[1200];
    snprintf(path, sizeof path, "%s/%016llx.dds", dir, (unsigned long long)hsh);
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

// Takes entry i out of the table (lock held) and returns it; release() frees it after the lock is left. Freeing an HD
// image reports it to vk_exec_image_gone, which calls snap_texpack_gone, which takes the lock: freed under the lock,
// the thread waited on itself (the game froze when a level released its light maps).
static HdTex take_locked(int i) {
    HdTex t = hd[i];
    hd[i] = hd[--nhd];
    __atomic_add_fetch(&gen, 1, __ATOMIC_RELAXED);
    return t;
}

static void release(HdTex t) {
    if (!t.img) return;
    vk_exec_image_gone(t.img);   // its views (get_view keeps them under the HD image)
    vk_defer_image(t.img, t.mem);
}

// The HD image for img (hash h) from dir, attached outside the lock; the previous one for img is freed.
static void attach(const VkTexImage *img, uint64_t h, int have, const char *dir, const char *what) {
    HdTex old = {0}, t;
    plat_mutex_lock(&lock);
    int at = -1;
    for (int i = 0; i < nhd; i++)
        if (hd[i].game == img->image) at = i;
    if (at >= 0 && hd[at].hash == h) { plat_mutex_unlock(&lock); return; }
    if (at >= 0) old = take_locked(at);
    plat_mutex_unlock(&lock);
    release(old);
    if (!have || !load(img, h, &t, dir)) return;   // outside the lock: the upload may free images
    plat_mutex_lock(&lock);
    int full = nhd >= HD_MAX;
    if (!full) hd[nhd++] = t, __atomic_add_fetch(&gen, 1, __ATOMIC_RELAXED);
    plat_mutex_unlock(&lock);
    if (full) { vk_defer_image(t.img, t.mem); return; }
    static int n[2];
    int k = dir == light_dir;
    if (n[k]++ < 3 || n[k] % 200 == 0) rt_log("texpack: %d %s in use (last %016llx, %ux%u -> %ux%u)", n[k], what,
                                              (unsigned long long)h, img->width, img->height, t.w, t.h);
}

// vk_texture.c upload, after the game's content went to img: hash it, dump it, attach or drop its HD image.
void snap_texpack_uploaded(const VkTexImage *img, const void *mem, uint64_t size, int nvn_format) {
    setup();
    if (!mem || !size) return;
    uint64_t seed = (uint64_t)img->width << 32 ^ (uint64_t)img->height << 16 ^ (uint64_t)(uint32_t)nvn_format;
    if (light_on && is_light_map(img)) {   // HD-SHADOW-01
        uint64_t h = hash_bytes(mem, size, seed);
        int have = in_light(h);
        attach(img, h, have, light_dir, "HD light maps");
        if (!have) dump_to(img, h, light_src, 1);
        return;
    }
    {   // NEWSNAP_TEX_WHITE=<vk format>[,<vk format>] (diagnostics): those textures drawn plain white, to find which
        // layer a part of the picture comes from (white.dds next to the game, written once)
        static int formats[4] = {-1, -1, -1, -1};
        static char white_dir[1100];
        if (formats[0] == -1) {
            const char *v = getenv("NEWSNAP_TEX_WHITE");
            formats[0] = -2;
            if (v && *v) sscanf(v, "%d,%d,%d,%d", &formats[0], &formats[1], &formats[2], &formats[3]);
        }
        if (formats[0] >= 0 && (formats[0] == (int)img->format || formats[1] == (int)img->format ||
                                formats[2] == (int)img->format || formats[3] == (int)img->format) &&
            img->type == VK_IMAGE_TYPE_2D && img->layers == 1 && !img->skip) {
            uint64_t h = hash_bytes(mem, size, seed);
            if (!white_dir[0]) {
                char exe[900];
                if (plat_exe_path(exe, sizeof exe)) {
                    char *slash = strrchr(exe, '/'), *bs = strrchr(exe, 92);
                    if (bs && (!slash || bs > slash)) slash = bs;
                    if (slash) *slash = 0;
                    snprintf(white_dir, sizeof white_dir, "%s/texwhite", exe);
                    plat_fs_mkdir(white_dir);
                }
            }
            char path[1200];
            snprintf(path, sizeof path, "%s/%016llx.dds", white_dir, (unsigned long long)h);
            FILE *f = fopen(path, "rb");
            if (f) fclose(f);
            else if ((f = fopen(path, "wb"))) {
                uint8_t hdr[148] = {0}, px[64];
                uint32_t v;
                memcpy(hdr, "DDS ", 4);
                v = 124, memcpy(hdr + 4, &v, 4); v = 0x100F, memcpy(hdr + 8, &v, 4);
                v = 4, memcpy(hdr + 12, &v, 4), memcpy(hdr + 16, &v, 4); v = 16, memcpy(hdr + 20, &v, 4);
                v = 1, memcpy(hdr + 28, &v, 4); v = 32, memcpy(hdr + 76, &v, 4); v = 4, memcpy(hdr + 80, &v, 4);
                memcpy(hdr + 84, "DX10", 4); v = 0x1000, memcpy(hdr + 108, &v, 4);
                v = 28, memcpy(hdr + 128, &v, 4); v = 3, memcpy(hdr + 132, &v, 4); v = 1, memcpy(hdr + 140, &v, 4);
                memset(px, 255, sizeof px);
                fwrite(hdr, 1, sizeof hdr, f), fwrite(px, 1, sizeof px, f);
                fclose(f);
            }
            attach(img, h, 1, white_dir, "white diagnostic textures");
            return;
        }
    }
    if (dump_dir[0] && dump_all() && eligible_data(img)) {
        dump(img, hash_bytes(mem, size, seed));
        return;
    }
    if (!eligible(img) || (!dump_dir[0] && nindex <= 0 && !nhd)) return;
    uint64_t h = hash_bytes(mem, size, seed);
    if (dump_dir[0]) dump(img, h);
    attach(img, h, in_pack(h), pack_dir, "HD textures");
}

void snap_texpack_gone(VkImage game) {
    if (!nhd) return;
    HdTex gone[8];
    int n = 0;
    plat_mutex_lock(&lock);
    for (int i = 0; i < nhd && n < 8; i++)
        if (hd[i].game == game) gone[n++] = take_locked(i--);
    plat_mutex_unlock(&lock);
    for (int i = 0; i < n; i++) release(gone[i]);
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

// The in-game menu (MENU-02): how many HD textures the pack folder holds, 0 for none.
int snap_texpack_files(void) {
    setup();
    return nindex > 0 ? nindex : 0;
}
