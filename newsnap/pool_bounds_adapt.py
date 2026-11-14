"""Opt-in pool-image bounds experiment; no claim of AMD photo causality."""

ORIGINAL = '''static int bind_pool_memory(VkCtx *c, Tex *e, VkImage img, uint64_t guest_size) {
    VkMemoryRequirements req;
    vkGetImageMemoryRequirements(c->device, img, &req);
    if ((e->f.depth || e->f.stencil) && req.size > guest_size) return 0;
    VkMemSpan sp;
    if (!req.size) return 0;   // an image the device could not lay out (image_size)
    if (!vk_mem_resolve(e->pub.addr, req.size, &sp) || !sp.alloc || sp.alloc_offset % req.alignment) return 0;
    VmaAllocationInfo info;
    vmaGetAllocationInfo(c->vma, sp.alloc, &info);
    if (!(req.memoryTypeBits >> info.memoryType & 1)) return 0;
    if (vmaBindImageMemory2(c->vma, sp.alloc, sp.alloc_offset, img, NULL) != VK_SUCCESS) return 0;
    e->bound_to = sp.alloc;
    return 1;
}'''

SUPPORT = r'''// SNAP_POOL_BOUNDS: diagnostic experiment, not a vendor-specific workaround.
// Cache the startup environment once. Concurrent first callers may compute the
// same value, but only a completed value is published; no partially initialized
// state, spin wait or per-image environment reads after publication.
static int snap_pool_bounds_enabled(void) {
    static int state;
    int value = __atomic_load_n(&state, __ATOMIC_ACQUIRE);
    if (!value) {
        const char *setting = getenv("AC_SNAP_POOL_BOUNDS");
        int chosen = setting && !strcmp(setting, "1") ? 2 : 1;
        int expected = 0;
        __atomic_compare_exchange_n(&state, &expected, chosen, 0, __ATOMIC_RELEASE, __ATOMIC_RELAXED);
        value = __atomic_load_n(&state, __ATOMIC_ACQUIRE);
    }
    return value == 2;
}

static int snap_pool_bounds_result(const Tex *e, VkImage img, const VkMemoryRequirements *req,
                                   uint64_t guest_size, const VkMemSpan *span, int memory_type,
                                   int result, const char *decision) {
    static unsigned reported_colour, reported_depth;
    if (req->size <= guest_size) return result;
    int depth = e->f.depth || e->f.stencil;
    unsigned *reported = depth ? &reported_depth : &reported_colour;
    unsigned limit = depth ? 4 : 16;
    unsigned count = __atomic_load_n(reported, __ATOMIC_RELAXED);
    do {
        if (count >= limit) return result;
    } while (!__atomic_compare_exchange_n(reported, &count, count + 1, 1,
                                          __ATOMIC_RELAXED, __ATOMIC_RELAXED));
    rt_log("pool_bounds: image=%#llx addr=%#llx nvn_fmt=%#x vk_fmt=%d dims=%ux%u "
           "guest_size=%llu req_size=%llu alignment=%llu type_bits=%#x memory_type=%d "
           "span_known=%d alloc_offset=%llu avail=%llu decision=%s bound=%d",
           (unsigned long long)(uintptr_t)img, (unsigned long long)e->pub.addr,
           e->t.d.format, (int)e->f.vk, e->t.d.width, e->t.d.height,
           (unsigned long long)guest_size, (unsigned long long)req->size,
           (unsigned long long)req->alignment, req->memoryTypeBits, memory_type,
           span != NULL, (unsigned long long)(span ? span->alloc_offset : 0),
           (unsigned long long)(span ? span->avail : 0), decision, result);
    return result;
}

'''

REPLACEMENT = r'''static int bind_pool_memory(VkCtx *c, Tex *e, VkImage img, uint64_t guest_size) {
    VkMemoryRequirements req;
    vkGetImageMemoryRequirements(c->device, img, &req);
    if ((e->f.depth || e->f.stencil) && req.size > guest_size)
        return snap_pool_bounds_result(e, img, &req, guest_size, NULL, -1, 0, "policy_depth");
    if (req.size > guest_size && snap_pool_bounds_enabled())
        return snap_pool_bounds_result(e, img, &req, guest_size, NULL, -1, 0, "policy_optin");
    VkMemSpan sp;
    if (!req.size) return 0;   // an image the device could not lay out (image_size)
    if (!vk_mem_resolve(e->pub.addr, req.size, &sp))
        return snap_pool_bounds_result(e, img, &req, guest_size, NULL, -1, 0, "unresolved");
    if (!sp.alloc)
        return snap_pool_bounds_result(e, img, &req, guest_size, &sp, -1, 0, "no_allocation");
    if (sp.alloc_offset % req.alignment)
        return snap_pool_bounds_result(e, img, &req, guest_size, &sp, -1, 0, "alignment");
    VmaAllocationInfo info;
    vmaGetAllocationInfo(c->vma, sp.alloc, &info);
    if (!(req.memoryTypeBits >> info.memoryType & 1))
        return snap_pool_bounds_result(e, img, &req, guest_size, &sp, info.memoryType, 0, "memory_type");
    if (vmaBindImageMemory2(c->vma, sp.alloc, sp.alloc_offset, img, NULL) != VK_SUCCESS)
        return snap_pool_bounds_result(e, img, &req, guest_size, &sp, info.memoryType, 0, "bind_failed");
    e->bound_to = sp.alloc;
    return snap_pool_bounds_result(e, img, &req, guest_size, &sp, info.memoryType, 1, "bound");
}'''


def edits():
    return {'runtime/vk_texture.c': [(ORIGINAL, SUPPORT + REPLACEMENT)]}
