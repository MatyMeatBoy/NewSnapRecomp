// FG-01: AMD FSR frame generation, off by default (snap_fsr_fg.h).
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cfg.h"
#include "host.h"
#include "vk.h"
#include "platform/platform.h"
#include "snap_fsr_sdk.h"
#include "snap_fsr_fg.h"

double gfx_window_refresh_hz(void);   // gfx_present.c

#include "snap_fg_rate.h"

int snap_fg_rate_ok(uint64_t interval_ns) {
    static int state = 1;
    static uint64_t since;
    double real = interval_ns ? 1e9 / (double)interval_ns : 0, panel = gfx_window_refresh_hz();
    int next = snap_fg_rate_decide(real, panel, state, kern_now_ns(), &since);
    if (next != state)
        rt_log("frame generation: %s (real %.1f fps, monitor %.1f Hz; generated frames need about %.0f Hz)",
               next ? "on again" : "paused, the monitor cannot show the generated frames", real, panel, real / 0.55);
    return state = next;
}

float snap_fg_view[16];   // vk_dlaa.c mv_pass

int snap_fg_mode(void) {
    static int mode = -1;
    if (mode < 0) {
        const char *v = cfg_value("AC_FRAME_GEN");
        mode = v && !strcmp(v, "fsr") ? 1 : v && !strcmp(v, "dlss") ? 2 : 0;
        if (mode) rt_log("frame generation: %s, one generated frame between real ones (AC_FRAME_GEN=%s)",
                         mode == 1 ? "FSR" : "NVIDIA DLSS", v);
    }
    return mode;
}

int snap_fg_enabled(void) { return snap_fg_mode() != 0; }

#if defined(_WIN32) && defined(NEWSNAP_FSR_SDK)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdbool.h>
#include <stddef.h>
#include <api/include/ffx_api.h>
#include <api/include/vk/ffx_api_vk.h>
#include <framegeneration/include/ffx_framegeneration.h>
#include "snap_dlssg.h"

static PlatMutex fg_lock;   // the context is used from the replay thread (prepare) and the present thread
static struct {
    HMODULE module;
    PfnFfxCreateContext create;
    PfnFfxDestroyContext destroy;
    PfnFfxConfigure configure;
    PfnFfxDispatch dispatch;
    int tried, fails;
    ffxContext ctx;
    uint32_t dw, dh, rw, rh;
    VkFormat fmt;
    struct ffxCreateBackendVKDesc backend;
    struct ffxCreateContextDescFrameGeneration desc;
    uint64_t next_id, prepared, taken, armed;
    int reset;
    VkImage out;
    VmaAllocation out_mem;
    VkFormat out_fmt;
    uint32_t ow, oh;
} G;

static int load(void) {
    if (G.tried) return G.module != NULL;
    G.tried = 1;
    wchar_t path[32768];
    DWORD n = GetModuleFileNameW(NULL, path, 32768);
    wchar_t *end = n && n < 32768 ? wcsrchr(path, L'\\') : NULL;
    const wchar_t suffix[] = L"\\upscalers\\amd_fidelityfx_framegeneration_vk.dll";
    if (!end || (size_t)(end - path) + sizeof suffix / sizeof *suffix > 32768) return 0;
    memcpy(end, suffix, sizeof suffix);
    G.module = LoadLibraryExW(path, NULL, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!G.module) {
        rt_log("frame generation: upscalers\\amd_fidelityfx_framegeneration_vk.dll not found: off");
        return 0;
    }
    G.create = (PfnFfxCreateContext)GetProcAddress(G.module, "ffxCreateContext");
    G.destroy = (PfnFfxDestroyContext)GetProcAddress(G.module, "ffxDestroyContext");
    G.configure = (PfnFfxConfigure)GetProcAddress(G.module, "ffxConfigure");
    G.dispatch = (PfnFfxDispatch)GetProcAddress(G.module, "ffxDispatch");
    if (!G.create || !G.destroy || !G.configure || !G.dispatch) {
        rt_log("frame generation: the FidelityFX frame generation DLL lacks its API: off");
        FreeLibrary(G.module);
        G.module = NULL;
        return 0;
    }
    return 1;
}

static uint32_t ffx_format(VkFormat f) {
    switch (f) {
    case VK_FORMAT_R32_SFLOAT: case VK_FORMAT_D32_SFLOAT: return FFX_API_SURFACE_FORMAT_R32_FLOAT;
    case VK_FORMAT_R16G16_SFLOAT: return FFX_API_SURFACE_FORMAT_R16G16_FLOAT;
    case VK_FORMAT_R16G16B16A16_SFLOAT: return FFX_API_SURFACE_FORMAT_R16G16B16A16_FLOAT;
    case VK_FORMAT_R8G8B8A8_UNORM: return FFX_API_SURFACE_FORMAT_R8G8B8A8_UNORM;
    case VK_FORMAT_R8G8B8A8_SRGB: return FFX_API_SURFACE_FORMAT_R8G8B8A8_SRGB;
    case VK_FORMAT_B8G8R8A8_UNORM: return FFX_API_SURFACE_FORMAT_B8G8R8A8_UNORM;
    case VK_FORMAT_B8G8R8A8_SRGB: return FFX_API_SURFACE_FORMAT_B8G8R8A8_SRGB;
    default: return FFX_API_SURFACE_FORMAT_UNKNOWN;
    }
}

// Snap's window textures are sRGB; FFX reads and writes them as UNORM bytes (the transfer
// function says SRGB), through views the runtime's MUTABLE_FORMAT colour images allow.
static VkFormat unorm(VkFormat f) {
    return f == VK_FORMAT_R8G8B8A8_SRGB ? VK_FORMAT_R8G8B8A8_UNORM : f == VK_FORMAT_B8G8R8A8_SRGB ? VK_FORMAT_B8G8R8A8_UNORM : f;
}

static struct FfxApiResource res(VkImage image, VkFormat f, uint32_t w, uint32_t h, int uav, int depth) {
    struct FfxApiResource r;
    memset(&r, 0, sizeof r);
    if (!image) return r;
    r.resource = (void *)(uintptr_t)image;
    r.state = uav ? FFX_API_RESOURCE_STATE_UNORDERED_ACCESS : FFX_API_RESOURCE_STATE_COMPUTE_READ;
    r.description.type = FFX_API_RESOURCE_TYPE_TEXTURE2D;
    r.description.format = ffx_format(f);
    r.description.width = w;
    r.description.height = h;
    r.description.depth = 1;
    r.description.mipCount = 1;
    r.description.usage = (uav ? FFX_API_RESOURCE_USAGE_UAV : FFX_API_RESOURCE_USAGE_READ_ONLY) |
                          (depth ? FFX_API_RESOURCE_USAGE_DEPTHTARGET : 0);
    return r;
}

static void wait_idle(void) {
    vk_queue_lock();
    vkDeviceWaitIdle(vk_ctx()->device);
    vk_queue_unlock();
}

static void destroy_locked(void) {
    if (G.ctx) {
        wait_idle();
        G.destroy(&G.ctx, NULL);
        G.ctx = NULL;
    }
}

static int create_locked(uint32_t dw, uint32_t dh, uint32_t rw, uint32_t rh, VkFormat fmt) {
    destroy_locked();
    const VkCtx *c = vk_ctx();
    memset(&G.backend, 0, sizeof G.backend);
    G.backend.header.type = FFX_API_CREATE_CONTEXT_DESC_TYPE_BACKEND_VK;
    G.backend.deviceContext.vkDevice = c->device;
    G.backend.deviceContext.vkPhysicalDevice = c->phys;
    G.backend.deviceContext.vkDeviceProcAddr = vkGetDeviceProcAddr;
    memset(&G.desc, 0, sizeof G.desc);
    G.desc.header.type = FFX_API_CREATE_CONTEXT_DESC_TYPE_FRAMEGENERATION;
    G.desc.header.pNext = &G.backend.header;
    G.desc.flags = FFX_FRAMEGENERATION_ENABLE_DEPTH_INVERTED | FFX_FRAMEGENERATION_ENABLE_DEPTH_INFINITE;
    G.desc.displaySize.width = dw;
    G.desc.displaySize.height = dh;
    G.desc.maxRenderSize.width = rw;
    G.desc.maxRenderSize.height = rh;
    G.desc.backBufferFormat = ffx_format(fmt);
    uint64_t t0 = kern_now_ns();
    ffxReturnCode_t r = G.create(&G.ctx, &G.desc.header, NULL);
    if (r != FFX_API_RETURN_OK) {
        G.ctx = NULL;
        if (G.fails++ < 4) rt_log("frame generation: context %ux%u (render %ux%u, format %d) failed (%u)", dw, dh, rw, rh, (int)fmt, (unsigned)r);
        return 0;
    }
    struct ffxConfigureDescFrameGeneration cf;
    memset(&cf, 0, sizeof cf);
    cf.header.type = FFX_API_CONFIGURE_DESC_TYPE_FRAMEGENERATION;
    cf.frameGenerationEnabled = true;
    cf.flags = FFX_FRAMEGENERATION_FLAG_NO_SWAPCHAIN_CONTEXT_NOTIFY;
    cf.generationRect.width = (int32_t)dw;
    cf.generationRect.height = (int32_t)dh;
    cf.frameID = G.next_id;
    r = G.configure(&G.ctx, &cf.header);
    if (r != FFX_API_RETURN_OK) {
        if (G.fails++ < 4) rt_log("frame generation: configure failed (%u)", (unsigned)r);
        G.destroy(&G.ctx, NULL);
        G.ctx = NULL;
        return 0;
    }
    G.dw = dw, G.dh = dh, G.rw = rw, G.rh = rh, G.fmt = fmt;
    G.reset = 1;
    rt_log("frame generation: FSR context %ux%u (render up to %ux%u, format %d), in %.1f ms",
           dw, dh, rw, rh, (int)fmt, (kern_now_ns() - t0) / 1e6);
    return 1;
}

// The game camera's view matrix of the frame (vk_dlaa.c mv_pass stores it; 0 before the first).
// The axes are its rotation rows; the translation sits in the last column (row-major) or the
// last row (column-major): the larger of the two is taken. FSR 3.1.4+ uses these to see cuts.
static void camera_vectors(float pos[3], float right[3], float up[3], float fwd[3]) {
    float v[16];
    memcpy(v, snap_fg_view, sizeof v);
    float tc[3] = {v[3], v[7], v[11]}, tr[3] = {v[12], v[13], v[14]};
    int col = fabsf(tc[0]) + fabsf(tc[1]) + fabsf(tc[2]) >= fabsf(tr[0]) + fabsf(tr[1]) + fabsf(tr[2]);
    float r[3][3];
    for (int a = 0; a < 3; a++)
        for (int b = 0; b < 3; b++) r[a][b] = col ? v[a * 4 + b] : v[b * 4 + a];
    const float *t = col ? tc : tr;
    for (int a = 0; a < 3; a++) {
        right[a] = r[0][a], up[a] = r[1][a], fwd[a] = -r[2][a];
        pos[a] = -(r[0][a] * t[0] + r[1][a] * t[1] + r[2][a] * t[2]);
    }
    if (!(right[0] || right[1] || right[2])) right[0] = 1, up[1] = 1, fwd[2] = 1;   // no camera yet
}

void snap_fg_prepare(VkCommandBuffer cb, const SnapFsrFrame *f, uint32_t render_w, uint32_t render_h,
                     uint32_t output_w, uint32_t output_h) {
    if (snap_fg_mode() != 1 || !f || !load()) return;
    plat_mutex_lock(&fg_lock);
    if (G.fails > 3) goto out;
    // The back buffer's format is known at the first generation; until then RGBA8 (Snap's window textures).
    VkFormat fmt = G.fmt ? G.fmt : VK_FORMAT_R8G8B8A8_UNORM;
    if (!G.ctx || G.dw != output_w || G.dh != output_h || render_w > G.rw || render_h > G.rh)
        if (!create_locked(output_w, output_h, render_w > G.rw ? render_w : G.rw ? G.rw : render_w,
                           render_h > G.rh ? render_h : G.rh ? G.rh : render_h, fmt)) goto out;
    uint64_t id = ++G.next_id;
    struct ffxDispatchDescFrameGenerationPrepareV2 pd;
    memset(&pd, 0, sizeof pd);
    pd.header.type = FFX_API_DISPATCH_DESC_TYPE_FRAMEGENERATION_PREPARE_V2;
    pd.frameID = id;
    pd.flags = 0;
    pd.commandList = (void *)cb;
    pd.renderSize.width = render_w;
    pd.renderSize.height = render_h;
    pd.jitterOffset.x = f->jitter_x;
    pd.jitterOffset.y = f->jitter_y;
    pd.motionVectorScale.x = f->motion_scale_x;
    pd.motionVectorScale.y = f->motion_scale_y;
    pd.frameTimeDelta = f->delta_ms > 0 ? f->delta_ms : 16.67f;
    pd.reset = G.reset || f->reset;
    pd.cameraNear = f->camera_near;
    pd.cameraFar = f->camera_far;
    pd.cameraFovAngleVertical = f->vertical_fov;
    pd.viewSpaceToMetersFactor = f->meters_factor > 0 ? f->meters_factor : 1.f;
    camera_vectors(pd.cameraPosition, pd.cameraRight, pd.cameraUp, pd.cameraForward);
    pd.depth = res(f->depth.image, f->depth.format, f->depth.width, f->depth.height, 0, 1);
    pd.motionVectors = res(f->motion.image, f->motion.format, f->motion.width, f->motion.height, 0, 0);
    ffxReturnCode_t r = G.dispatch(&G.ctx, &pd.header);
    if (r != FFX_API_RETURN_OK) {
        if (G.fails++ < 4) rt_log("frame generation: prepare failed (%u)", (unsigned)r);
        goto out;
    }
    G.prepared = id;
out:
    plat_mutex_unlock(&fg_lock);
}

uint64_t snap_fg_take(void) {
    if (!snap_fg_enabled()) return 0;
    plat_mutex_lock(&fg_lock);
    uint64_t id = G.prepared > G.taken ? G.prepared : 0;
    if (id) G.taken = id;
    plat_mutex_unlock(&fg_lock);
    return id;
}

void snap_fg_arm(uint64_t id) {
    plat_mutex_lock(&fg_lock);
    G.armed = id;
    plat_mutex_unlock(&fg_lock);
}

static int output_locked(VkFormat fmt, uint32_t w, uint32_t h) {
    if (G.out && G.out_fmt == fmt && G.ow == w && G.oh == h) return 1;
    const VkCtx *c = vk_ctx();
    if (G.out) {
        wait_idle();
        vmaDestroyImage(c->vma, G.out, G.out_mem);
        G.out = VK_NULL_HANDLE;
    }
    VkFormatProperties fp;
    vkGetPhysicalDeviceFormatProperties(c->phys, fmt, &fp);
    if (!(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT)) {
        if (G.fails++ < 4) rt_log("frame generation: format %d cannot be a storage image here", (int)fmt);
        return 0;
    }
    VkImageCreateInfo ii = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D, .format = fmt,
                            .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT,
                            .tiling = VK_IMAGE_TILING_OPTIMAL, .flags = VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT,
                            .usage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT |
                                     VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &ii, &ai, &G.out, &G.out_mem, NULL) != VK_SUCCESS) {
        G.out = VK_NULL_HANDLE;
        if (G.fails++ < 4) rt_log("frame generation: output image %ux%u failed", w, h);
        return 0;
    }
    G.out_fmt = fmt, G.ow = w, G.oh = h;
    G.reset = 1;
    return 1;
}

static void barrier(VkCommandBuffer cb, VkImage img, VkImageLayout from, VkImageLayout to, VkAccessFlags src, VkAccessFlags dst) {
    VkImageMemoryBarrier b = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .srcAccessMask = src, .dstAccessMask = dst,
                              .oldLayout = from, .newLayout = to, .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                              .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .image = img,
                              .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1}};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, NULL, 0, NULL, 1, &b);
}

// The replay's command buffer belongs to the recorder thread (vk_rec.h): vkCmdPipelineBarrier is not one of its
// wrapped calls and would be made at once, ahead of the copies queued before it and while the recorder writes the same
// command buffer. These two use vkCmdPipelineBarrier2, which the recorder makes in call order. Replay thread only.
static void replay_layout_general(VkCommandBuffer cb, VkImage img, VkImageAspectFlags aspect) {
    VkImageMemoryBarrier2 b = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
                               .srcStageMask = VK_PIPELINE_STAGE_2_NONE, .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                               .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT,
                               .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                               .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                               .image = img, .subresourceRange = {aspect, 0, 1, 0, 1}};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = 1, .pImageMemoryBarriers = &b};
    vkCmdPipelineBarrier2(cb, &di);
}

static void replay_sync(VkCommandBuffer cb) {   // what was written so far is visible to what follows, and the reverse
    VkMemoryBarrier2 mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER_2,
                           .srcStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                           .srcAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT,
                           .dstStageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT,
                           .dstAccessMask = VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT};
    VkDependencyInfo di = {.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .memoryBarrierCount = 1, .pMemoryBarriers = &mb};
    vkCmdPipelineBarrier2(cb, &di);
}

// FG-02: the HUD-less picture. Snap tonemaps the scene into a full-size RGBA8_SRGB target and the next pass draws the
// interface over it into the RGBA8 picture that is presented. When that next pass begins, the tonemapped target is
// complete: it is copied (same bytes, UNORM) to a ring slot of the frame's prepare id, and the generation dispatch of
// that frame gets it as HUDLessColor, so FFX keeps the interface out of the interpolation (no HUD trails). Matched by
// format and size, no vendor branch. Replay thread (vk_exec.c vk_exec_pass_begin).
static volatile uint64_t fg_generated;   // generated frames dispatched (FG-03)
uint64_t snap_fg_generated_count(void) { return __atomic_load_n(&fg_generated, __ATOMIC_RELAXED); }

#define HUDLESS_N 3
static struct { VkImage img; VmaAllocation mem; uint32_t w, h; uint64_t id; } HL[HUDLESS_N];
static VkImage hl_src;
static uint32_t hl_w, hl_h;

static int hl_slot_locked(int i, uint32_t w, uint32_t h, VkCommandBuffer cb) {
    if (HL[i].img && HL[i].w == w && HL[i].h == h) return 1;
    const VkCtx *c = vk_ctx();
    if (HL[i].img) vk_defer_image(HL[i].img, HL[i].mem), HL[i].img = VK_NULL_HANDLE;
    VkImageCreateInfo ii = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D,
                            .format = VK_FORMAT_R8G8B8A8_UNORM, .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1,
                            .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                            .usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                            .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(c->vma, &ii, &ai, &HL[i].img, &HL[i].mem, NULL) != VK_SUCCESS) {
        HL[i].img = VK_NULL_HANDLE;
        return 0;
    }
    HL[i].w = w, HL[i].h = h, HL[i].id = 0;
    replay_layout_general(cb, HL[i].img, VK_IMAGE_ASPECT_COLOR_BIT);
    return 1;
}

void snap_fg_hudless_pass(VkCommandBuffer cb, const VkTexImage *img, VkFormat view) {
    if (!img || !snap_fg_enabled() || img->type != VK_IMAGE_TYPE_2D || img->layers > 1) return;
    // The tonemap pass draws the full-size RGBA8_SRGB image through an sRGB view; the interface pass then draws into
    // the same image (same storage) through a UNORM view. At that second begin the image holds the scene without HUD.
    if (img->format == VK_FORMAT_R8G8B8A8_SRGB && view == VK_FORMAT_R8G8B8A8_SRGB && img->width >= 640) {
        hl_src = img->image, hl_w = img->width, hl_h = img->height;
        return;
    }
    if (!hl_src || img->image != hl_src || view != VK_FORMAT_R8G8B8A8_UNORM) return;
    VkImage src = hl_src;
    hl_src = VK_NULL_HANDLE;
    plat_mutex_lock(&fg_lock);
    uint64_t id = G.prepared;
    int i = (int)(id % HUDLESS_N);
    if (id && (G.ctx || snap_fg_mode() == 2) && hl_slot_locked(i, hl_w, hl_h, cb)) {
        replay_sync(cb);
        VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .extent = {hl_w, hl_h, 1}};
        vkCmdCopyImage(cb, src, VK_IMAGE_LAYOUT_GENERAL, HL[i].img, VK_IMAGE_LAYOUT_GENERAL, 1, &rg);
        replay_sync(cb);
        HL[i].id = id;
    }
    plat_mutex_unlock(&fg_lock);
}

static void hudless_configure_locked(uint64_t id, uint32_t w, uint32_t h, VkCommandBuffer cb, VkImage *used) {
    *used = VK_NULL_HANDLE;
    int i = (int)(id % HUDLESS_N);
    struct ffxConfigureDescFrameGeneration cf;
    memset(&cf, 0, sizeof cf);
    cf.header.type = FFX_API_CONFIGURE_DESC_TYPE_FRAMEGENERATION;
    cf.frameGenerationEnabled = true;
    cf.flags = FFX_FRAMEGENERATION_FLAG_NO_SWAPCHAIN_CONTEXT_NOTIFY;
    cf.generationRect.width = (int32_t)w;
    cf.generationRect.height = (int32_t)h;
    cf.frameID = id;
    if (HL[i].img && HL[i].id == id && HL[i].w == w && HL[i].h == h) {
        barrier(cb, HL[i].img, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                VK_ACCESS_MEMORY_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
        cf.HUDLessColor = res(HL[i].img, VK_FORMAT_R8G8B8A8_UNORM, w, h, 0, 0);
        *used = HL[i].img;
    }
    static int state = -1;
    if (G.configure(&G.ctx, &cf.header) != FFX_API_RETURN_OK) {
        if (*used) barrier(cb, *used, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL,
                           VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT);
        *used = VK_NULL_HANDLE;
        return;
    }
    static int changes;
    if (state != (*used != VK_NULL_HANDLE) && changes++ < 8) {   // menus have no tonemap pass: no HUD-less image there
        state = *used != VK_NULL_HANDLE;
        rt_log("frame generation: %s", state ? "HUD-less image from the tonemapped scene (no HUD trails)"
                                              : "no HUD-less image this frame");
    }
}

// ---- FG-DLSS: NVIDIA DLSS frame generation (snap_dlssg.h) ---------------------------------------------------------
// DLSS takes the real picture, the depth and the motion vectors of the frame in one call, on the present thread, while
// the replay may already be drawing the next frame over its depth: so the replay copies both into a ring slot of the
// frame's id when DLSS Super Resolution has run (snap_fg_prepare_dlss), as it does for the HUD-less picture.
static struct {
    VkImage z, mv;
    VmaAllocation z_mem, mv_mem;
    VkImageView z_view, mv_view;
    VkFormat z_fmt;
    uint32_t w, h, ow, oh;
    uint64_t id;
    float jx, jy;
    int reset;
    SnapDlssgCamera cam;
} DR[HUDLESS_N];
static struct { VkImage img; VmaAllocation mem; VkImageView view; uint32_t w, h; } BB;   // the real picture, as UNORM bytes
static struct { VkImage of; VkImageView view; } DV[HUDLESS_N], OV;                          // views of HL[i].img and G.out

static VkImageAspectFlags depth_aspects(VkFormat f) {
    return f == VK_FORMAT_D24_UNORM_S8_UINT || f == VK_FORMAT_D32_SFLOAT_S8_UINT || f == VK_FORMAT_D16_UNORM_S8_UINT
               ? VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT : VK_IMAGE_ASPECT_DEPTH_BIT;
}

static VkImageView make_view(VkImage img, VkFormat f, VkImageAspectFlags aspect) {
    VkImageViewCreateInfo vi = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = img,
                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = f, .subresourceRange = {aspect, 0, 1, 0, 1}};
    VkImageView v = VK_NULL_HANDLE;
    return vkCreateImageView(vk_ctx()->device, &vi, NULL, &v) == VK_SUCCESS ? v : VK_NULL_HANDLE;
}

static void drop(VkImage *img, VmaAllocation *mem, VkImageView *view) {   // after wait_idle
    const VkCtx *c = vk_ctx();
    if (*view) vkDestroyImageView(c->device, *view, NULL), *view = VK_NULL_HANDLE;
    if (*img) vmaDestroyImage(c->vma, *img, *mem), *img = VK_NULL_HANDLE;
}

static int make_image(VkFormat f, uint32_t w, uint32_t h, VkImageUsageFlags usage, VkImageAspectFlags view_aspect,
                      VkImage *img, VmaAllocation *mem, VkImageView *view) {
    VkImageCreateInfo ii = {.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .imageType = VK_IMAGE_TYPE_2D, .format = f,
                            .extent = {w, h, 1}, .mipLevels = 1, .arrayLayers = 1, .samples = VK_SAMPLE_COUNT_1_BIT,
                            .tiling = VK_IMAGE_TILING_OPTIMAL, .usage = usage, .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED};
    VmaAllocationCreateInfo ai = {.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE};
    if (vmaCreateImage(vk_ctx()->vma, &ii, &ai, img, mem, NULL) != VK_SUCCESS) {
        *img = VK_NULL_HANDLE;
        return 0;
    }
    *view = make_view(*img, f, view_aspect);
    if (!*view) {
        vmaDestroyImage(vk_ctx()->vma, *img, *mem), *img = VK_NULL_HANDLE;
        return 0;
    }
    return 1;
}

static void layout_general(VkCommandBuffer cb, VkImage img, VkImageAspectFlags aspect) {
    VkImageMemoryBarrier b = {.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
                              .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                              .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                              .image = img, .subresourceRange = {aspect, 0, 1, 0, 1}};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, NULL, 0, NULL, 1, &b);
}

static void sync(VkCommandBuffer cb) {   // everything written so far is visible to what follows, and the reverse
    VkMemoryBarrier mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
                          .srcAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT,
                          .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 1, &mb, 0, NULL, 0, NULL);
}

void snap_fg_prepare_dlss(VkCommandBuffer cb, VkImage depth, VkFormat depth_format, uint32_t level, uint32_t layer,
                          VkImage motion, uint32_t w, uint32_t h, uint32_t ow, uint32_t oh, float jitter_x,
                          float jitter_y, int reset) {
    if (snap_fg_mode() != 2 || !depth || !motion || !w || !h) return;
    plat_mutex_lock(&fg_lock);
    if (G.fails > 3) goto out;
    uint64_t id = G.next_id + 1;
    int i = (int)(id % HUDLESS_N);
    if (DR[i].z && (DR[i].w != w || DR[i].h != h || DR[i].z_fmt != depth_format)) {
        wait_idle();
        drop(&DR[i].z, &DR[i].z_mem, &DR[i].z_view), drop(&DR[i].mv, &DR[i].mv_mem, &DR[i].mv_view);
    }
    if (!DR[i].z) {
        VkImageAspectFlags da = depth_aspects(depth_format);
        if (!make_image(depth_format, w, h, VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                        VK_IMAGE_ASPECT_DEPTH_BIT, &DR[i].z, &DR[i].z_mem, &DR[i].z_view) ||
            !make_image(VK_FORMAT_R16G16_SFLOAT, w, h, VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                        VK_IMAGE_ASPECT_COLOR_BIT, &DR[i].mv, &DR[i].mv_mem, &DR[i].mv_view)) {
            drop(&DR[i].z, &DR[i].z_mem, &DR[i].z_view);
            if (G.fails++ < 4) rt_log("frame generation: DLSS depth and motion copies %ux%u (depth format %d) failed", w, h, (int)depth_format);
            goto out;
        }
        DR[i].w = w, DR[i].h = h, DR[i].z_fmt = depth_format;
        replay_layout_general(cb, DR[i].z, da), replay_layout_general(cb, DR[i].mv, VK_IMAGE_ASPECT_COLOR_BIT);
    }
    replay_sync(cb);
    VkImageCopy zc = {.srcSubresource = {VK_IMAGE_ASPECT_DEPTH_BIT, level, layer, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_DEPTH_BIT, 0, 0, 1}, .extent = {w, h, 1}};
    vkCmdCopyImage(cb, depth, VK_IMAGE_LAYOUT_GENERAL, DR[i].z, VK_IMAGE_LAYOUT_GENERAL, 1, &zc);
    VkImageCopy mc = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .extent = {w, h, 1}};
    vkCmdCopyImage(cb, motion, VK_IMAGE_LAYOUT_GENERAL, DR[i].mv, VK_IMAGE_LAYOUT_GENERAL, 1, &mc);
    replay_sync(cb);
    DR[i].id = id, DR[i].ow = ow, DR[i].oh = oh, DR[i].jx = jitter_x, DR[i].jy = jitter_y, DR[i].reset = reset;
    snap_dlssg_camera(&DR[i].cam);
    camera_vectors(DR[i].cam.pos, DR[i].cam.right, DR[i].cam.up, DR[i].cam.fwd);
    G.next_id = id, G.prepared = id;
out:
    plat_mutex_unlock(&fg_lock);
}

static VkImage dlss_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    fmt = unorm(fmt);
    plat_mutex_lock(&fg_lock);
    VkImage result = VK_NULL_HANDLE;
    uint64_t id = G.armed;
    G.armed = 0;
    int i = (int)(id % HUDLESS_N);
    if (!id || G.fails > 3 || DR[i].id != id || !DR[i].z) goto out;
    if ((uint32_t)w != DR[i].ow || (uint32_t)h != DR[i].oh) goto out;   // a picture of another size: no generated frame
    if (fmt != VK_FORMAT_R8G8B8A8_UNORM && fmt != VK_FORMAT_B8G8R8A8_UNORM) goto out;
    if (!output_locked(fmt, (uint32_t)w, (uint32_t)h)) goto out;
    if (OV.of != G.out) {
        if (OV.view) wait_idle(), vkDestroyImageView(vk_ctx()->device, OV.view, NULL);
        OV.view = make_view(G.out, fmt, VK_IMAGE_ASPECT_COLOR_BIT), OV.of = OV.view ? G.out : VK_NULL_HANDLE;
        if (!OV.view) goto out;
    }
    if (BB.img && (BB.w != (uint32_t)w || BB.h != (uint32_t)h)) wait_idle(), drop(&BB.img, &BB.mem, &BB.view);
    if (!BB.img) {
        if (!make_image(fmt, (uint32_t)w, (uint32_t)h, VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                        VK_IMAGE_ASPECT_COLOR_BIT, &BB.img, &BB.mem, &BB.view)) {
            if (G.fails++ < 4) rt_log("frame generation: DLSS picture copy %dx%d failed", w, h);
            goto out;
        }
        BB.w = (uint32_t)w, BB.h = (uint32_t)h;
        layout_general(cb, BB.img, VK_IMAGE_ASPECT_COLOR_BIT);
        G.reset = 1;
    }
    barrier(cb, G.out, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL, 0, VK_ACCESS_SHADER_WRITE_BIT);
    sync(cb);
    VkImageCopy pc = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .extent = {(uint32_t)w, (uint32_t)h, 1}};
    vkCmdCopyImage(cb, src, VK_IMAGE_LAYOUT_GENERAL, BB.img, VK_IMAGE_LAYOUT_GENERAL, 1, &pc);   // the window's own cb: made at once
    sync(cb);
    SnapDlssgFrame f = {.backbuffer = {BB.img, BB.view, fmt, (uint32_t)w, (uint32_t)h},
                        .depth = {DR[i].z, DR[i].z_view, DR[i].z_fmt, DR[i].w, DR[i].h},
                        .mv = {DR[i].mv, DR[i].mv_view, VK_FORMAT_R16G16_SFLOAT, DR[i].w, DR[i].h},
                        .out = {G.out, OV.view, fmt, (uint32_t)w, (uint32_t)h},
                        .jitter_x = DR[i].jx, .jitter_y = DR[i].jy, .reset = G.reset || DR[i].reset, .cam = DR[i].cam};
    static int hud_state = -1, hud_changes;
    int hud = HL[i].img && HL[i].id == id && HL[i].w == (uint32_t)w && HL[i].h == (uint32_t)h && fmt == VK_FORMAT_R8G8B8A8_UNORM;
    if (hud) {
        if (DV[i].of != HL[i].img) {
            if (DV[i].view) wait_idle(), vkDestroyImageView(vk_ctx()->device, DV[i].view, NULL);
            DV[i].view = make_view(HL[i].img, VK_FORMAT_R8G8B8A8_UNORM, VK_IMAGE_ASPECT_COLOR_BIT);
            DV[i].of = DV[i].view ? HL[i].img : VK_NULL_HANDLE;
        }
        if (DV[i].view) f.hudless = (SnapDlssgImage){HL[i].img, DV[i].view, VK_FORMAT_R8G8B8A8_UNORM, (uint32_t)w, (uint32_t)h};
        else hud = 0;
    }
    if (hud_state != hud && hud_changes++ < 8) {
        hud_state = hud;
        rt_log("frame generation: %s", hud ? "HUD-less image from the tonemapped scene (no HUD trails)" : "no HUD-less image this frame");
    }
    static int test = -1;   // NEWSNAP_DLSSG_TEST (diagnostics): 1 no HUD-less image, 2 with OutputReal, 8 no evaluation
    if (test < 0) { const char *t = getenv("NEWSNAP_DLSSG_TEST"); test = t ? atoi(t) : 0; }
    if (test & 1) f.hudless.image = VK_NULL_HANDLE;
    static VkImage rl; static VmaAllocation rl_mem; static VkImageView rl_view;
    if ((test & 2) && !rl && make_image(fmt, (uint32_t)w, (uint32_t)h, VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, VK_IMAGE_ASPECT_COLOR_BIT, &rl, &rl_mem, &rl_view))
        layout_general(cb, rl, VK_IMAGE_ASPECT_COLOR_BIT);
    if ((test & 2) && rl) f.real = (SnapDlssgImage){rl, rl_view, fmt, (uint32_t)w, (uint32_t)h};
    int ok = test & 8 ? 0 : snap_dlssg_generate(cb, &f);
    sync(cb);
    if (test & 8) goto out;
    if (!ok) {
        G.fails++;
        goto out;
    }
    G.reset = 0;
    result = G.out;
    __atomic_add_fetch(&fg_generated, 1, __ATOMIC_RELAXED);
    static int logged;
    if (!logged) logged = 1, rt_log("frame generation: first DLSS generated frame %dx%d (frame id %llu)", w, h, (unsigned long long)id);
out:
    plat_mutex_unlock(&fg_lock);
    return result;
}

// NEWSNAP_FG_SHOTS=<folder> (diagnostics): from generated frame NEWSNAP_FG_SHOTS_FROM on, every 300th generated frame
// is saved as the window shows it (gen-<n>.png), with the real frames shown before and after it (real-<n>a.png,
// real-<n>b.png), to look at what the generation makes. Present thread.
void vk_present_shot(const char *path);   // gfx_present.c: the picture of the present being recorded
static void fg_shot(int generated) {
    static const char *dir;
    static int init, pending;
    static uint64_t from, n, at;
    if (!init) {
        init = 1;
        dir = getenv("NEWSNAP_FG_SHOTS");
        const char *f = getenv("NEWSNAP_FG_SHOTS_FROM");
        from = f ? strtoull(f, NULL, 10) : 0;
        if (dir && !*dir) dir = NULL;
        if (dir) plat_fs_mkdir(dir);
    }
    if (!dir) return;
    char path[1200];
    if (generated) {
        n++;
        if (pending == 1) {   // the generated frame after the real one that was saved
            snprintf(path, sizeof path, "%s/gen-%llu.png", dir, (unsigned long long)at);
            vk_present_shot(path);
            pending = 2;
        }
        return;
    }
    if (pending == 2) {
        snprintf(path, sizeof path, "%s/real-%llub.png", dir, (unsigned long long)at);
        vk_present_shot(path);
        pending = 0;
    } else if (!pending && n >= from && n % 300 == 0 && n != at) {
        at = n;
        snprintf(path, sizeof path, "%s/real-%llua.png", dir, (unsigned long long)at);
        vk_present_shot(path);
        pending = 1;
    }
}

static VkImage fsr_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h);

VkImage snap_fg_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    if (!snap_fg_enabled() || !src || w <= 0 || h <= 0) return VK_NULL_HANDLE;
    VkImage made = snap_fg_mode() == 2 ? dlss_present_source(cb, src, fmt, w, h) : fsr_present_source(cb, src, fmt, w, h);
    fg_shot(made != VK_NULL_HANDLE);
    return made;
}

static VkImage fsr_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    fmt = unorm(fmt);
    plat_mutex_lock(&fg_lock);
    VkImage result = VK_NULL_HANDLE;
    uint64_t id = G.armed;
    G.armed = 0;
    if (!id || !G.ctx || G.fails > 3) goto out;
    if (fmt != G.fmt && G.fmt) {   // a different back buffer: a new context, from the next prepare on
        G.fmt = fmt;
        destroy_locked();
        goto out;
    }
    G.fmt = fmt;
    if ((uint32_t)w != G.dw || (uint32_t)h != G.dh) goto out;   // a picture of another size: no generated frame for it
    if (!output_locked(fmt, (uint32_t)w, (uint32_t)h)) goto out;
    barrier(cb, src, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            VK_ACCESS_MEMORY_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
    barrier(cb, G.out, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL, 0, VK_ACCESS_SHADER_WRITE_BIT);
    struct ffxDispatchDescFrameGeneration gd;
    memset(&gd, 0, sizeof gd);
    gd.header.type = FFX_API_DISPATCH_DESC_TYPE_FRAMEGENERATION;
    gd.commandList = (void *)cb;
    gd.presentColor = res(src, fmt, (uint32_t)w, (uint32_t)h, 0, 0);
    gd.outputs[0] = res(G.out, fmt, (uint32_t)w, (uint32_t)h, 1, 0);
    gd.numGeneratedFrames = 1;
    gd.reset = G.reset;
    gd.backbufferTransferFunction = FFX_API_BACKBUFFER_TRANSFER_FUNCTION_SRGB;   // Snap's SDR picture
    gd.minMaxLuminance[0] = 0.f;
    gd.minMaxLuminance[1] = 1.f;
    gd.generationRect.width = w;
    gd.generationRect.height = h;
    gd.frameID = id;
    VkImage hl_used;
    hudless_configure_locked(id, (uint32_t)w, (uint32_t)h, cb, &hl_used);
    ffxReturnCode_t r = G.dispatch(&G.ctx, &gd.header);
    if (hl_used) barrier(cb, hl_used, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL,
                         VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT);
    barrier(cb, src, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL,
            VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT);
    barrier(cb, G.out, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
            VK_ACCESS_SHADER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT | VK_ACCESS_SHADER_READ_BIT);
    if (r != FFX_API_RETURN_OK) {
        if (G.fails++ < 4) rt_log("frame generation: dispatch failed (%u)", (unsigned)r);
        goto out;
    }
    G.reset = 0;
    result = G.out;
    __atomic_add_fetch(&fg_generated, 1, __ATOMIC_RELAXED);   // FG-03: the performance overlay's FG rate
    static int logged;
    if (!logged) logged = 1, rt_log("frame generation: first generated frame %dx%d (frame id %llu)", w, h, (unsigned long long)id);
out:
    plat_mutex_unlock(&fg_lock);
    return result;
}

void snap_fg_release(void) {
    if (snap_fg_mode() == 2) {   // FG-DLSS: the device is idle here (gfx_present.c release)
        plat_mutex_lock(&fg_lock);
        snap_dlssg_release();
        for (int i = 0; i < HUDLESS_N; i++) {
            drop(&DR[i].z, &DR[i].z_mem, &DR[i].z_view), drop(&DR[i].mv, &DR[i].mv_mem, &DR[i].mv_view);
            if (DV[i].view) vkDestroyImageView(vk_ctx()->device, DV[i].view, NULL), DV[i].view = VK_NULL_HANDLE;
            if (HL[i].img) vmaDestroyImage(vk_ctx()->vma, HL[i].img, HL[i].mem), HL[i].img = VK_NULL_HANDLE;
        }
        drop(&BB.img, &BB.mem, &BB.view);
        if (OV.view) vkDestroyImageView(vk_ctx()->device, OV.view, NULL), OV.view = VK_NULL_HANDLE;
        if (G.out) { vmaDestroyImage(vk_ctx()->vma, G.out, G.out_mem); G.out = VK_NULL_HANDLE; }
        plat_mutex_unlock(&fg_lock);
        return;
    }
    if (!G.module) return;
    plat_mutex_lock(&fg_lock);
    if (G.ctx) { G.destroy(&G.ctx, NULL); G.ctx = NULL; }
    if (G.out) { vmaDestroyImage(vk_ctx()->vma, G.out, G.out_mem); G.out = VK_NULL_HANDLE; }
    for (int i = 0; i < HUDLESS_N; i++)
        if (HL[i].img) vmaDestroyImage(vk_ctx()->vma, HL[i].img, HL[i].mem), HL[i].img = VK_NULL_HANDLE;
    plat_mutex_unlock(&fg_lock);
}

#else
void snap_fg_prepare(VkCommandBuffer cb, const SnapFsrFrame *f, uint32_t rw, uint32_t rh, uint32_t ow, uint32_t oh) {
    (void)cb; (void)f; (void)rw; (void)rh; (void)ow; (void)oh;
}
uint64_t snap_fg_take(void) { return 0; }
void snap_fg_prepare_dlss(VkCommandBuffer cb, VkImage depth, VkFormat depth_format, uint32_t level, uint32_t layer,
                          VkImage motion, uint32_t w, uint32_t h, uint32_t ow, uint32_t oh, float jitter_x,
                          float jitter_y, int reset) {
    (void)cb; (void)depth; (void)depth_format; (void)level; (void)layer; (void)motion; (void)w; (void)h; (void)ow;
    (void)oh; (void)jitter_x; (void)jitter_y; (void)reset;
}
void snap_dlssg_release(void);
void snap_fg_arm(uint64_t id) { (void)id; }
VkImage snap_fg_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    (void)cb; (void)src; (void)fmt; (void)w; (void)h;
    return VK_NULL_HANDLE;
}
void snap_fg_release(void) {}
uint64_t snap_fg_generated_count(void) { return 0; }
void snap_fg_hudless_pass(VkCommandBuffer cb, const VkTexImage *img, VkFormat view) { (void)cb; (void)img; (void)view; }
#endif
