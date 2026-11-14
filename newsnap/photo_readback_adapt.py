"""Safe host-import coherence, always-on photo copy statistics and opt-in images.

Manual imports require visible/coherent memory; incompatible pools use existing
VMA-managed shadow storage with explicit flush/invalidate. This independently
proven contract fix does not establish the cause of the owner's AMD photo bands.

Every photo-sized texture-to-buffer copy logs, without any setting, whether the
source image and the bytes that reached the destination buffer agree and where
either is black (16-pixel tiles). PNG files are still written only when
NEWSNAP_PHOTO_TRACE_DIR is set. Managed shadow storage remains an explicit
AC_SHADOW=1 experiment on native Windows; no vendor-specific default is changed.
Diagnostic staging is best-effort and limited to 64 MiB pending per session.
"""

IMPORT_SUPPORT = r'''
// Direct host pointers have no Vulkan map/flush/invalidate ownership here.
// Keep unsupported imports in managed storage, per pool, without forcing the
// normal coherent imports to change policy. The indicator only enables shadow
// synchronization/completion work when an automatic fallback exists.
static volatile int32_t snap_shadow_fallback;
static int snap_shadow_active(void) {
    return shadow_on || __atomic_load_n(&snap_shadow_fallback, __ATOMIC_ACQUIRE);
}
static void snap_import_report(const VkCtx *c, int type, uint32_t compatible, uint64_t alignment) {
    static unsigned reported;
    const char *trace = getenv("NEWSNAP_PHOTO_TRACE_DIR");
    if (!trace || !*trace) return;
    unsigned count = __atomic_load_n(&reported, __ATOMIC_RELAXED);
    do {
        if (count >= 8) return;
    } while (!__atomic_compare_exchange_n(&reported, &count, count + 1, 1,
                                          __ATOMIC_RELAXED, __ATOMIC_RELAXED));
    rt_log("photo_trace: host import type=%d properties=%#x compatible_bits=%#x min_alignment=%llu", type,
           type < 0 ? 0 : c->mem_props.memoryTypes[type].propertyFlags, compatible, (unsigned long long)alignment);
}
'''

COMMON = r'''
// FOTO-01: bounded statistics; local images only when explicitly enabled.
// Diagnostic staging is owned until completion, independently of guest memory.
static int snap_photo_format(VkFormat format) {
    return format == VK_FORMAT_R8G8B8A8_UNORM || format == VK_FORMAT_R8G8B8A8_SRGB ? 1 :
           format == VK_FORMAT_B8G8R8A8_UNORM || format == VK_FORMAT_B8G8R8A8_SRGB ? 2 : 0;
}
static void snap_photo_pair(const char *directory, const char *path, unsigned number, uint64_t frame,
                            uint32_t w, uint32_t h, VkFormat format,
                            const uint8_t *source, size_t source_pitch, const uint8_t *copy, size_t copy_pitch) {
    // directory NULL or empty: statistics in the log only, no files.
    int files = directory && *directory;
    if (!w || !h || w > 8192 || h > 8192 ||
            (uint64_t)w * h > 4u * 1024u * 1024u || !snap_photo_format(format)) return;
    size_t row = (size_t)w * 4, bytes = row * h;
    if (source_pitch < row || copy_pitch < row) return;
    uint8_t *rgba = malloc(bytes);
    if (!rgba) return;
    // 16-pixel tiles with any non-black texel, per image: a band that covers
    // only part of a row does not show in black_rows.
    uint32_t tw = (w + 15) / 16, th = (h + 15) / 16;
    size_t tiles = (size_t)tw * th;
    uint8_t *lit = calloc(2, tiles);
    if (!lit) { free(rgba); return; }
    uint64_t mismatch = 0, hash[2] = {14695981039346656037ull, 14695981039346656037ull};
    unsigned black[2] = {0};
    const uint8_t *inputs[2] = {source, copy};
    size_t pitches[2] = {source_pitch, copy_pitch};
    if (files) plat_file_mkdir_p(directory);
    for (int image = 0; image < 2; image++) {
        for (uint32_t y = 0; y < h; y++) {
            const uint8_t *in = inputs[image] + (size_t)y * pitches[image];
            int empty = 1;
            for (uint32_t x = 0; x < w; x++) {
                uint8_t *out = rgba + ((size_t)y * w + x) * 4;
                for (unsigned c = 0; c < 4; c++) {
                    unsigned component = snap_photo_format(format) == 2 && c < 3 ? 2 - c : c;
                    uint8_t value = in[(size_t)x * 4 + component];
                    out[c] = c == 3 ? 255 : value;
                    hash[image] = (hash[image] ^ value) * 1099511628211ull;
                    if (c < 3 && value) empty = 0, lit[image * tiles + (size_t)(y / 16) * tw + x / 16] = 1;
                    if (!image && in[(size_t)x * 4 + c] != copy[(size_t)y * copy_pitch + (size_t)x * 4 + c]) mismatch++;
                }
            }
            black[image] += empty;
        }
        if (!files) continue;
        char filename[1024];
        int length = snprintf(filename, sizeof filename, "%s/%s-%02u-f%llu-%s.png", directory, path, number,
                              (unsigned long long)frame, image ? "buffer" : "source");
        if (length > 0 && (size_t)length < sizeof filename) rt_write_png(filename, rgba, w, h);
    }
    // Black tiles per image and the first runs of black tiles in the buffer
    // (tile row y, pixel columns x0-x1): the geometry of a band, for the log.
    unsigned dark[2] = {0};
    char bands[400] = "none";
    size_t used = 0;
    unsigned runs = 0;
    for (int image = 0; image < 2; image++)
        for (uint32_t ty = 0; ty < th; ty++)
            for (uint32_t tx = 0; tx < tw; tx++) {
                if (lit[image * tiles + (size_t)ty * tw + tx]) continue;
                dark[image]++;
                if (!image || (tx && !lit[tiles + (size_t)ty * tw + tx - 1])) continue;
                uint32_t end = tx;
                while (end + 1 < tw && !lit[tiles + (size_t)ty * tw + end + 1]) end++;
                if (runs++ < 10 && used < sizeof bands - 40)
                    used += (size_t)snprintf(bands + used, sizeof bands - used, "%sy%u:x%u-%u", used ? " " : "",
                                             ty * 16, tx * 16, end * 16 + 15 < w ? end * 16 + 15 : w - 1);
            }
    rt_log("photo_trace: %s %u frame %llu %ux%u fmt %d pitches %llu/%llu mismatch_bytes=%llu "
           "black_rows=%u/%u hashes=%016llx/%016llx black_tiles16=%u/%u of %u buffer_black_runs=%u [%s]%s",
           path, number, (unsigned long long)frame, w, h, (int)format,
           (unsigned long long)source_pitch, (unsigned long long)copy_pitch, (unsigned long long)mismatch,
           black[0], black[1], (unsigned long long)hash[0], (unsigned long long)hash[1], dark[0], dark[1],
           (unsigned)tiles, runs, bands, files ? "" : " (log only)");
    free(lit);
    free(rgba);
}
'''

CONTEXT = r'''
// FOTO-01: what the photo copy reads and where it writes, in the normal log.
// 24 lines a run at most; reads no guest memory and records no GPU work.
static void snap_photo_context(const Sub *s, uint64_t address, uint64_t size, const VkMemSpan *before,
                               const VkMemSpan *picked) {
    static unsigned lines;
    if (lines >= 24 || !snap_photo_format(s->img->format) || s->nz != 1 || s->w < 128 || s->h < 96) return;
    lines++;
    uint32_t uploads = 0;
    int last_change = 0, pages_written = 0;
    vk_texture_debug(s->img, &uploads, &last_change, &pages_written);
    const char *upscaler = vk_dlaa_running();
    rt_log("photo_log: copy %u frame %llu source %#llx %ux%u vk_fmt %d gpu_owned %d cpu_storage %d uploads %u "
           "storage_written_since %d; destination %#llx bytes %llu class %d through %s; upscaler %s", lines - 1,
           (unsigned long long)__atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED),
           (unsigned long long)s->img->addr, s->w, s->h, (int)s->img->format, s->img->gpu_owned, s->img->mirrored,
           uploads, pages_written, (unsigned long long)address, (unsigned long long)size, picked->cls,
           !picked->pool ? "device memory" : picked->buffer != before->buffer ? "a device-local mirror"
                                                                              : "the pool's own buffer",
           upscaler ? upscaler : "none");
}
'''

GPU = COMMON + r'''
typedef struct {
    VkBuffer source_buffer, copy_buffer;
    VmaAllocation source_alloc, copy_alloc;
    uint8_t *source, *copy;
    uint32_t w, h;
    size_t pitch;
    VkFormat format;
    uint64_t frame;
    unsigned number;
    char directory[1024];
    uint64_t reserved_bytes;
} SnapPhotoTransfer;
#define SNAP_PHOTO_PENDING_MAX (64ull << 20)
static uint64_t snap_photo_pending_bytes;
static int snap_photo_reserve(uint64_t bytes) {
    uint64_t old = __atomic_load_n(&snap_photo_pending_bytes, __ATOMIC_RELAXED);
    do {
        if (bytes > SNAP_PHOTO_PENDING_MAX || old > SNAP_PHOTO_PENDING_MAX - bytes) return 0;
    } while (!__atomic_compare_exchange_n(&snap_photo_pending_bytes, &old, old + bytes, 1,
                                          __ATOMIC_RELAXED, __ATOMIC_RELAXED));
    return 1;
}
static int snap_photo_staging(VkDeviceSize size, VkBuffer *buffer, VmaAllocation *allocation, uint8_t **mapping) {
    VkBufferCreateInfo bi = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = size,
        .usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_HOST,
        .flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_RANDOM_BIT | VMA_ALLOCATION_CREATE_MAPPED_BIT};
    VmaAllocationInfo info;
    VkCtx *c = vk_ctx();
    if (vmaCreateBuffer(c->vma, &bi, &ai, buffer, allocation, &info) != VK_SUCCESS) return 0;
    if (!info.pMappedData) {
        vmaDestroyBuffer(c->vma, *buffer, *allocation);
        return 0;
    }
    *mapping = info.pMappedData;
    return 1;
}
static void snap_photo_release(SnapPhotoTransfer *trace) {
    __atomic_fetch_sub(&snap_photo_pending_bytes, trace->reserved_bytes, __ATOMIC_RELAXED);
    free(trace);
}
static void snap_photo_transfer_done(void *argument) {
    SnapPhotoTransfer *trace = argument;
    VkCtx *c = vk_ctx();
    vmaInvalidateAllocation(c->vma, trace->source_alloc, 0, VK_WHOLE_SIZE);
    vmaInvalidateAllocation(c->vma, trace->copy_alloc, 0, VK_WHOLE_SIZE);
    snap_photo_pair(trace->directory, "gpu-t2b", trace->number, trace->frame, trace->w, trace->h, trace->format,
                    trace->source, (size_t)trace->w * 4, trace->copy, trace->pitch);
    vmaDestroyBuffer(c->vma, trace->source_buffer, trace->source_alloc);
    vmaDestroyBuffer(c->vma, trace->copy_buffer, trace->copy_alloc);
    snap_photo_release(trace);
}
static void snap_photo_trace_t2b(VkExec *ex, const Sub *s, uint64_t size,
                                const VkBufferImageCopy *original, const VkMemSpan *destination) {
    const char *directory = getenv("NEWSNAP_PHOTO_TRACE_DIR");
    static unsigned captures;
    if (captures >= (directory && *directory ? 8u : 24u) || !snap_photo_format(s->img->format) ||
            s->nz != 1 || s->img->samples != 1 || s->w < 128 || s->h < 96 ||
            s->w > 8192 || s->h > 8192 || (uint64_t)s->w * s->h > 4u * 1024u * 1024u ||
            !size || size > 32u * 1024u * 1024u) return;
    size_t row = (size_t)s->w * 4;
    size_t pitch = original->bufferRowLength ? (size_t)original->bufferRowLength * 4 : row;
    if (pitch < row || (uint64_t)pitch * (s->h - 1) + row > size) return;
    uint64_t reserved = (uint64_t)row * s->h + size;
    if (!snap_photo_reserve(reserved)) return;
    SnapPhotoTransfer *trace = calloc(1, sizeof *trace);
    if (!trace) {
        __atomic_fetch_sub(&snap_photo_pending_bytes, reserved, __ATOMIC_RELAXED);
        return;
    }
    trace->reserved_bytes = reserved;
    trace->w = s->w, trace->h = s->h, trace->pitch = pitch, trace->format = s->img->format;
    trace->frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    trace->number = captures;
    int length = snprintf(trace->directory, sizeof trace->directory, "%s", directory ? directory : "");
    if (length < 0 || (size_t)length >= sizeof trace->directory) { snap_photo_release(trace); return; }
    if (!snap_photo_staging(row * s->h, &trace->source_buffer, &trace->source_alloc, &trace->source)) {
        snap_photo_release(trace);
        return;
    }
    if (!snap_photo_staging(size, &trace->copy_buffer, &trace->copy_alloc, &trace->copy)) {
        vmaDestroyBuffer(vk_ctx()->vma, trace->source_buffer, trace->source_alloc);
        snap_photo_release(trace);
        return;
    }
    captures++;
    VkBufferImageCopy tight = *original;
    tight.bufferOffset = 0, tight.bufferRowLength = 0, tight.bufferImageHeight = 0;
    vkCmdCopyImageToBuffer(ex->cb, s->img->image, VK_IMAGE_LAYOUT_GENERAL, trace->source_buffer, 1, &tight);
    // The original transfer wrote the destination: make those bytes visible to
    // this diagnostic read without accessing mutable/freed guest CPU addresses.
    VkMemoryBarrier2 memory = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2,
        .srcStageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT, .srcAccessMask = VK_ACCESS_2_TRANSFER_WRITE_BIT,
        .dstStageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT, .dstAccessMask = VK_ACCESS_2_TRANSFER_READ_BIT};
    VkDependencyInfo dependency = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO,
                                   .memoryBarrierCount = 1, .pMemoryBarriers = &memory};
    vkCmdPipelineBarrier2(ex->cb, &dependency);
    VkBufferCopy range = {destination->offset, 0, size};
    vkCmdCopyBuffer(ex->cb, destination->buffer, trace->copy_buffer, 1, &range);
    memory.dstStageMask = VK_PIPELINE_STAGE_2_HOST_BIT;
    memory.dstAccessMask = VK_ACCESS_2_HOST_READ_BIT;
    vkCmdPipelineBarrier2(ex->cb, &dependency);
    vk_completion_add(ex->fence, snap_photo_transfer_done, trace);
    ex->recorded += 2;
    rt_log("photo_trace: queued gpu-t2b %u frame %llu source_addr=%#llx source_fmt=%d "
           "region=%d,%d %ux%u stride=%llu bytes=%llu fence=%llu", trace->number,
           (unsigned long long)trace->frame, (unsigned long long)s->img->addr, (int)trace->format,
           s->x, s->y, s->w, s->h, (unsigned long long)pitch, (unsigned long long)size,
           (unsigned long long)ex->fence);
}
'''

CPU = COMMON + r'''
static void snap_photo_trace_cpu(const Tex *e, const Region *g, const NVNcopyRegion *region,
                                  const uint8_t *staging, const uint8_t *output) {
    const char *directory = getenv("NEWSNAP_PHOTO_TRACE_DIR");
    static unsigned captures;
    if (!directory || !*directory || captures >= 8 || g->nz != 1 || g->bw != 1 || g->bh != 1 || g->bpb != 4 ||
            region->width < 128 || region->height < 96 || region->width > 8192 || region->height > 8192 ||
            (uint64_t)region->width * region->height > 4u * 1024u * 1024u || !snap_photo_format(e->pub.format)) return;
    uint64_t frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    snap_photo_pair(directory, "cpu-read", captures++, frame, (uint32_t)region->width, (uint32_t)region->height,
                    e->pub.format, staging, g->wb, output, g->row);
}
'''


def edits():
    return {'runtime/vk_exec_xfer.c': [
        ('#include "vk_exec.h"',
         '#include "vk_exec.h"\n#include "gfx.h"\n#include "vk_dlaa.h"\n#include "platform/platform.h"'),
        ('static void copy_buffer_image(VkExec *ex, const p_copy_b2t *p, int to_image) {',
         GPU + CONTEXT + '\nstatic void copy_buffer_image(VkExec *ex, const p_copy_b2t *p, int to_image) {'),
        ('    VK_MEM_PICK(m);\n    *span = m;',
         '    VkMemSpan snap_before_pick = m;\n    VK_MEM_PICK(m);\n    *span = m;\n'
         '    if (c) snap_photo_span_before = snap_before_pick;'),
        ('    else vk_mem_gpu_wrote(&m, size), note_gpu_write(ex, p->src, size);',
         '    else vk_mem_gpu_wrote(&m, size), note_gpu_write(ex, p->src, size);\n'
         '    if (!to_image) snap_photo_context(&s, p->src, size, &snap_photo_span_before, &m);\n'
         '    if (!to_image) snap_photo_trace_t2b(ex, &s, size, &c, &m);'),
        ('static VkImageSubresourceLayers sub_layers(const Sub *s) {',
         'static VkMemSpan snap_photo_span_before;   // replay thread: the span buffer_side resolved, before its mirror pick\n'
         'static VkImageSubresourceLayers sub_layers(const Sub *s) {'),
    ], 'runtime/vk_texture.c': [
        ('static int image_texels_at(Tex *e, const Region *g, const NVNcopyRegion *r, uint8_t *mem, int write) {',
         CPU + '\nstatic int image_texels_at(Tex *e, const Region *g, const NVNcopyRegion *r, uint8_t *mem, int write) {'),
        ('    free(rg);\n    vmaDestroyBuffer(c->vma, sb, sa);\n    return 1;',
         '    if (!write && !rgb && !astc) snap_photo_trace_cpu(e, g, r, stg, mem);\n'
         '    free(rg);\n    vmaDestroyBuffer(c->vma, sb, sa);\n    return 1;'),
    ], 'runtime/vk_memory.c': [
        ('static int shadow_on;                    // shadow mode: imported pools get shadow storage instead (vk_mem_class_log)',
         'static int shadow_on;                    // shadow mode: imported pools get shadow storage instead (vk_mem_class_log)\n' + IMPORT_SUPPORT),
        ('    for (uint32_t i = 0; i < c->mem_props.memoryTypeCount; i++)\n'
         '        if (bits >> i & 1) return (int)i;\n    return -1;',
         '    return -1; // Never waive required host visibility/coherence for direct guest pointers.'),
        ('    if (type < 0 || req.size > n) {',
         '    snap_import_report(c, type, req.memoryTypeBits & hp.memoryTypeBits, al);\n'
         '    if (type < 0) {\n'
         '        vkDestroyBuffer(c->device, r->buf, NULL);\n'
         '        r->buf = VK_NULL_HANDLE;\n'
         '        int managed = shadow_pool(c, r, addr, size);\n'
         '        if (managed) __atomic_store_n(&snap_shadow_fallback, 1, __ATOMIC_RELEASE);\n'
         '        rt_log("vk: pool %#llx: no coherent CPU-visible import type (compatible %#x, alignment %#llx); "\n'
         '               "managed shadow %s", (unsigned long long)addr, req.memoryTypeBits & hp.memoryTypeBits,\n'
         '               (unsigned long long)al, managed ? "enabled" : "allocation failed");\n'
         '        return managed;\n'
         '    }\n'
         '    if (req.size > n) {'),
        ('        if (shadow_on && h->pool && !((PoolRec *)h->pool)->stouched) shadow_touch(h->pool);',
         '        if (h->pool && ((PoolRec *)h->pool)->smap && !((PoolRec *)h->pool)->stouched) shadow_touch(h->pool);'),
        ('    rt_log("mem: mode %s (%s): %s", mode == 2 ? "verify" : mode ? "mirror" : "import", why,',
         '    {   // FOTO-01: the knobs of an AMD A/B session, as this run resolved them ("-": not set, default).\n'
         '        static const char *const knobs[] = {"AC_SHADOW", "AC_MEMORY", "AC_REPLAY_ASYNC", "AC_TEX_ALIAS",\n'
         '            "AC_TEX_PREFETCH", "AC_ASTC", "AC_ASTC_BC", "AC_PIPE_SKIP", "AC_GPL", "AC_VK_RECORDER",\n'
         '            "AC_UBO_SNAPSHOT", "AC_UPSCALING", "AC_VK_PRESENT", "AC_DUMP_KEY"};\n'
         '        char line[768];\n'
         '        size_t used = 0;\n'
         '        for (size_t i = 0; i < sizeof knobs / sizeof *knobs && used < sizeof line - 64; i++) {\n'
         '            const char *value = cfg_get(knobs[i]);\n'
         '            used += (size_t)snprintf(line + used, sizeof line - used, " %s=%.24s", knobs[i] + 3,\n'
         '                                     value && *value ? value : "-");\n'
         '        }\n'
         '        rt_log("amd_diag: shadow storage %s;%s", shadow_on ? "on" : "off", line);\n'
         '    }\n'
         '    rt_log("mem: mode %s (%s): %s", mode == 2 ? "verify" : mode ? "mirror" : "import", why,'),
        ('void vk_mem_shadow_sync(void) {\n    if (!shadow_on) return;',
         'void vk_mem_shadow_sync(void) {\n    if (!snap_shadow_active()) return;'),
        ('void vk_mem_gpu_pending(uint64_t addr, uint64_t size) {\n    if (!shadow_on || !size) return;',
         'void vk_mem_gpu_pending(uint64_t addr, uint64_t size) {\n    if (!snap_shadow_active() || !size) return;'),
        ('static void gpu_written(uint64_t addr, uint64_t size, int hold) {\n    if (shadow_on && size) {',
         'static void gpu_written(uint64_t addr, uint64_t size, int hold) {\n    if (snap_shadow_active() && size) {'),
        ('static void shadow_log(uint64_t frame) {\n    if (!shadow_on) return;',
         'static void shadow_log(uint64_t frame) {\n    if (!snap_shadow_active()) return;'),
        ('    nstouch = nspend = 0;   // shadows too',
         '    nstouch = nspend = 0;   // shadows too\n    __atomic_store_n(&snap_shadow_fallback, 0, __ATOMIC_RELEASE);'),
    ]}
