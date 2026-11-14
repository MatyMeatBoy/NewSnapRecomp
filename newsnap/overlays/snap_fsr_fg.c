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

int snap_fg_enabled(void) {
    static int on = -1;
    if (on < 0) {
        const char *v = cfg_value("AC_FRAME_GEN");
        on = v && !strcmp(v, "fsr");
        if (on) rt_log("frame generation: FSR, one generated frame between real ones (AC_FRAME_GEN=fsr)");
    }
    return on;
}

#if defined(_WIN32) && defined(NEWSNAP_FSR_SDK)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdbool.h>
#include <stddef.h>
#include <api/include/ffx_api.h>
#include <api/include/vk/ffx_api_vk.h>
#include <framegeneration/include/ffx_framegeneration.h>

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
    if (!snap_fg_enabled() || !f || !load()) return;
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

// FG-02: the HUD-less picture. Snap tonemaps the scene into a full-size RGBA8_SRGB target and the next pass draws the
// interface over it into the RGBA8 picture that is presented. When that next pass begins, the tonemapped target is
// complete: it is copied (same bytes, UNORM) to a ring slot of the frame's prepare id, and the generation dispatch of
// that frame gets it as HUDLessColor, so FFX keeps the interface out of the interpolation (no HUD trails). Matched by
// format and size, no vendor branch. Replay thread (vk_exec.c vk_exec_pass_begin).
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
    barrier(cb, HL[i].img, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT);
    return 1;
}

void snap_fg_hudless_pass(VkCommandBuffer cb, const VkTexImage *img) {
    if (!img || !snap_fg_enabled() || img->type != VK_IMAGE_TYPE_2D || img->layers > 1) return;
    if (img->format == VK_FORMAT_R8G8B8A8_SRGB && img->width >= 640) {   // a full-size tonemapped target begins
        hl_src = img->image, hl_w = img->width, hl_h = img->height;
        return;
    }
    if (!hl_src || img->format != VK_FORMAT_R8G8B8A8_UNORM || img->width != hl_w || img->height != hl_h) return;
    VkImage src = hl_src;
    hl_src = VK_NULL_HANDLE;
    plat_mutex_lock(&fg_lock);
    uint64_t id = G.prepared;
    int i = (int)(id % HUDLESS_N);
    if (id && G.ctx && hl_slot_locked(i, hl_w, hl_h, cb)) {
        VkMemoryBarrier mb = {.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER, .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,
                              .dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT | VK_ACCESS_TRANSFER_WRITE_BIT};
        vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 1, &mb, 0, NULL, 0, NULL);
        VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}, .extent = {hl_w, hl_h, 1}};
        vkCmdCopyImage(cb, src, VK_IMAGE_LAYOUT_GENERAL, HL[i].img, VK_IMAGE_LAYOUT_GENERAL, 1, &rg);
        mb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT, mb.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT;
        vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 1, &mb, 0, NULL, 0, NULL);
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
    if (state != (*used != VK_NULL_HANDLE)) {
        state = *used != VK_NULL_HANDLE;
        rt_log("frame generation: %s", state ? "HUD-less image from the tonemapped scene (no HUD trails)"
                                              : "no HUD-less image this frame");
    }
}

VkImage snap_fg_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    if (!snap_fg_enabled() || !src || w <= 0 || h <= 0) return VK_NULL_HANDLE;
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
    static int logged;
    if (!logged) logged = 1, rt_log("frame generation: first generated frame %dx%d (frame id %llu)", w, h, (unsigned long long)id);
out:
    plat_mutex_unlock(&fg_lock);
    return result;
}

void snap_fg_release(void) {
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
void snap_fg_arm(uint64_t id) { (void)id; }
VkImage snap_fg_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h) {
    (void)cb; (void)src; (void)fmt; (void)w; (void)h;
    return VK_NULL_HANDLE;
}
void snap_fg_release(void) {}
void snap_fg_hudless_pass(VkCommandBuffer cb, const VkTexImage *img) { (void)cb; (void)img; }
#endif
