"""Safe host-import coherence plus bounded opt-in GPU/CPU capture evidence.

Manual imports require visible/coherent memory; incompatible pools use existing
VMA-managed shadow storage with explicit flush/invalidate. This independently
proven contract fix does not establish the cause of the owner's AMD photo bands.
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
// FOTO-01: explicitly enabled, local diagnostic images only. At most eight
// captures per path; staging owned by diagnostics survives until its fence.
static int snap_photo_format(VkFormat format) {
    return format == VK_FORMAT_R8G8B8A8_UNORM || format == VK_FORMAT_R8G8B8A8_SRGB ? 1 :
           format == VK_FORMAT_B8G8R8A8_UNORM || format == VK_FORMAT_B8G8R8A8_SRGB ? 2 : 0;
}
static void snap_photo_pair(const char *directory, const char *path, unsigned number, uint64_t frame,
                            uint32_t w, uint32_t h, VkFormat format,
                            const uint8_t *source, size_t source_pitch, const uint8_t *copy, size_t copy_pitch) {
    if (!directory || !*directory || !w || !h || w > 8192 || h > 8192 ||
            (uint64_t)w * h > 4u * 1024u * 1024u || !snap_photo_format(format)) return;
    size_t row = (size_t)w * 4, bytes = row * h;
    if (source_pitch < row || copy_pitch < row) return;
    uint8_t *rgba = malloc(bytes);
    if (!rgba) return;
    uint64_t mismatch = 0, hash[2] = {14695981039346656037ull, 14695981039346656037ull};
    unsigned black[2] = {0};
    const uint8_t *inputs[2] = {source, copy};
    size_t pitches[2] = {source_pitch, copy_pitch};
    plat_file_mkdir_p(directory);
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
                    if (c < 3 && value) empty = 0;
                    if (!image && in[(size_t)x * 4 + c] != copy[(size_t)y * copy_pitch + (size_t)x * 4 + c]) mismatch++;
                }
            }
            black[image] += empty;
        }
        char filename[1024];
        int length = snprintf(filename, sizeof filename, "%s/%s-%02u-f%llu-%s.png", directory, path, number,
                              (unsigned long long)frame, image ? "buffer" : "source");
        if (length > 0 && (size_t)length < sizeof filename) rt_write_png(filename, rgba, w, h);
    }
    rt_log("photo_trace: %s %u frame %llu %ux%u fmt %d pitches %llu/%llu mismatch_bytes=%llu "
           "black_rows=%u/%u hashes=%016llx/%016llx", path, number, (unsigned long long)frame, w, h, (int)format,
           (unsigned long long)source_pitch, (unsigned long long)copy_pitch, (unsigned long long)mismatch,
           black[0], black[1], (unsigned long long)hash[0], (unsigned long long)hash[1]);
    free(rgba);
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
} SnapPhotoTransfer;
static void snap_photo_transfer_done(void *argument) {
    SnapPhotoTransfer *trace = argument;
    VkCtx *c = vk_ctx();
    vmaInvalidateAllocation(c->vma, trace->source_alloc, 0, VK_WHOLE_SIZE);
    vmaInvalidateAllocation(c->vma, trace->copy_alloc, 0, VK_WHOLE_SIZE);
    snap_photo_pair(trace->directory, "gpu-t2b", trace->number, trace->frame, trace->w, trace->h, trace->format,
                    trace->source, (size_t)trace->w * 4, trace->copy, trace->pitch);
    vmaDestroyBuffer(c->vma, trace->source_buffer, trace->source_alloc);
    vmaDestroyBuffer(c->vma, trace->copy_buffer, trace->copy_alloc);
    free(trace);
}
static void snap_photo_trace_t2b(VkExec *ex, const Sub *s, uint64_t size,
                                const VkBufferImageCopy *original, const VkMemSpan *destination) {
    const char *directory = getenv("NEWSNAP_PHOTO_TRACE_DIR");
    static unsigned captures;
    if (!directory || !*directory || captures >= 8 || !snap_photo_format(s->img->format) ||
            s->nz != 1 || s->img->samples != 1 || s->w < 128 || s->h < 96 ||
            s->w > 8192 || s->h > 8192 || (uint64_t)s->w * s->h > 4u * 1024u * 1024u ||
            !size || size > 32u * 1024u * 1024u) return;
    size_t row = (size_t)s->w * 4;
    size_t pitch = original->bufferRowLength ? (size_t)original->bufferRowLength * 4 : row;
    if (pitch < row || (uint64_t)pitch * (s->h - 1) + row > size) return;
    SnapPhotoTransfer *trace = calloc(1, sizeof *trace);
    if (!trace) return;
    trace->w = s->w, trace->h = s->h, trace->pitch = pitch, trace->format = s->img->format;
    trace->frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    trace->number = captures++;
    int length = snprintf(trace->directory, sizeof trace->directory, "%s", directory);
    if (length < 0 || (size_t)length >= sizeof trace->directory) { free(trace); return; }
    trace->source = vk_staging(row * s->h, &trace->source_buffer, &trace->source_alloc);
    trace->copy = vk_staging(size, &trace->copy_buffer, &trace->copy_alloc);
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
        ('#include "vk_exec.h"', '#include "vk_exec.h"\n#include "gfx.h"\n#include "platform/platform.h"'),
        ('static void copy_buffer_image(VkExec *ex, const p_copy_b2t *p, int to_image) {',
         GPU + '\nstatic void copy_buffer_image(VkExec *ex, const p_copy_b2t *p, int to_image) {'),
        ('    else vk_mem_gpu_wrote(&m, size), note_gpu_write(ex, p->src, size);',
         '    else vk_mem_gpu_wrote(&m, size), note_gpu_write(ex, p->src, size);\n'
         '    if (!to_image) snap_photo_trace_t2b(ex, &s, size, &c, &m);'),
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
