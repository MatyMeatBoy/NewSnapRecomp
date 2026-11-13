/* Optional official AMD SDK bridge. No donor scene addresses or inferred camera constants. */
#include "snap_fsr_sdk.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
int snap_fsr_sdk_int8_enabled;

static int image_ok(const SnapFsrImage *i, uint32_t w, uint32_t h, uint64_t generation, int output) {
    return i->image && i->width == w && i->height == h && i->generation == generation &&
        i->samples == 1 && i->layers == 1 && i->mips == 1 &&
        (output ? (i->layout == VK_IMAGE_LAYOUT_GENERAL && (i->usage & VK_IMAGE_USAGE_STORAGE_BIT)) :
         (i->layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL && (i->usage & VK_IMAGE_USAGE_SAMPLED_BIT)));
}

int snap_fsr_sdk_validate(const SnapFsrConfig *c, const SnapFsrFrame *f) {
    if (!c || !f || !c->device_contract_verified || !f->scene_contract_verified || !f->command_buffer ||
        !c->generation || !c->render_width || !c->render_height || !c->output_width || !c->output_height ||
        c->render_width > c->output_width || c->render_height > c->output_height) return 0;
    const SnapFsrImage *inputs[] = {&f->color, &f->depth, &f->motion};
    for (unsigned i = 0; i < 3; i++)
        if (!image_ok(inputs[i], c->render_width, c->render_height, c->generation, 0)) return 0;
    if (!image_ok(&f->output, c->output_width, c->output_height, c->generation, 1)) return 0;
    if (f->output.image == f->color.image || f->output.image == f->depth.image || f->output.image == f->motion.image) return 0;
    if (f->depth.format != VK_FORMAT_R32_SFLOAT && f->depth.format != VK_FORMAT_D32_SFLOAT) return 0;
    if (f->motion.format != VK_FORMAT_R16G16_SFLOAT && f->motion.format != VK_FORMAT_R32G32_SFLOAT) return 0;
    const SnapFsrImage *colors[] = {&f->color, &f->output};
    for (unsigned i = 0; i < 2; i++)
        if (colors[i]->format != VK_FORMAT_R16G16B16A16_SFLOAT && colors[i]->format != VK_FORMAT_R8G8B8A8_UNORM &&
            colors[i]->format != VK_FORMAT_B8G8R8A8_UNORM) return 0;
    if (!c->auto_exposure && !f->exposure.image) return 0;
    if (f->exposure.image && (!image_ok(&f->exposure, 1, 1, c->generation, 0) || f->exposure.format != VK_FORMAT_R32_SFLOAT)) return 0;
    const SnapFsrImage *masks[] = {&f->reactive, &f->transparency};
    for (unsigned i = 0; i < 2; i++)
        if (masks[i]->image && (!image_ok(masks[i], c->render_width, c->render_height, c->generation, 0) || masks[i]->format != VK_FORMAT_R8_UNORM)) return 0;
    const float scalars[] = {f->jitter_x, f->jitter_y, f->motion_scale_x, f->motion_scale_y, f->delta_ms,
        f->pre_exposure, f->camera_near, f->camera_far, f->vertical_fov, f->meters_factor};
    for (unsigned i = 0; i < sizeof scalars / sizeof *scalars; i++) if (!isfinite(scalars[i])) return 0;
    return f->delta_ms > 0 && f->pre_exposure > 0 && f->camera_near > 0 && f->meters_factor > 0 &&
        f->motion_scale_x != 0 && f->motion_scale_y != 0 && f->vertical_fov > 0 && f->vertical_fov < 3.141593f &&
        (c->infinite_depth || f->camera_far > f->camera_near);
}

#if defined(_WIN32) && defined(NEWSNAP_FSR_SDK)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdbool.h>
#include <stddef.h>
#include <api/include/ffx_api.h>
#include <api/include/vk/ffx_api_vk.h>
#include <upscalers/include/ffx_upscale.h>

struct SnapFsrSdk {
    HMODULE module;
    PfnFfxQuery query;
    PfnFfxCreateContext create;
    PfnFfxDestroyContext destroy;
    PfnFfxDispatch dispatch;
    ffxContext context;
    SnapFsrConfig config;
    /* SDK explicitly requires create descriptor pointers to live until destroy. */
    struct ffxCreateContextDescUpscale upscale;
    struct ffxCreateBackendVKDesc backend;
    struct ffxCreateContextDescUpscaleVersion version;
    struct ffxOverrideVersion override;
    uint32_t fresh;
};

SnapFsrSdk *snap_fsr_sdk_open(void) {
    wchar_t path[32768];
    DWORD n = GetModuleFileNameW(NULL, path, 32768);
    if (!n || n >= 32768) return NULL;
    wchar_t *end = wcsrchr(path, L'\\');
    const wchar_t suffix[] = L"\\upscalers\\amd_fidelityfx_upscaler_vk.dll";
    if (!end || (size_t)(end - path) + sizeof suffix / sizeof *suffix > 32768) return NULL;
    memcpy(end, suffix, sizeof suffix);
    /* Absolute path only; dependencies from this DLL's directory and System32. */
    HMODULE module = LoadLibraryExW(path, NULL, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!module) return NULL;
    SnapFsrSdk *s = calloc(1, sizeof *s);
    if (!s) { FreeLibrary(module); return NULL; }
    s->module = module;
    s->query = (PfnFfxQuery)GetProcAddress(module, "ffxQuery");
    s->create = (PfnFfxCreateContext)GetProcAddress(module, "ffxCreateContext");
    s->destroy = (PfnFfxDestroyContext)GetProcAddress(module, "ffxDestroyContext");
    s->dispatch = (PfnFfxDispatch)GetProcAddress(module, "ffxDispatch");
    if (!s->query || !s->create || !s->destroy || !s->dispatch) { snap_fsr_sdk_close(s); return NULL; }
    return s;
}

uint32_t snap_fsr_sdk_query(SnapFsrSdk *s, const SnapFsrDevice *d, SnapFsrProvider *out, uint32_t capacity) {
    if (!s || !d || !d->device || !d->physical_device || !d->get_device_proc || !out || !capacity) return 0;
    uint64_t ids[32], count = capacity < 32 ? capacity : 32;
    const char *names[32] = {0};
    VkDeviceContext device = {d->device, d->physical_device, d->get_device_proc};
    struct ffxQueryDescGetVersions q = {.header.type = FFX_API_QUERY_DESC_TYPE_GET_VERSIONS,
        .createDescType = FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE, .device = &device,
        .outputCount = &count, .versionIds = ids, .versionNames = names};
    if (s->query(NULL, &q.header) != FFX_API_RETURN_OK || count > capacity || count > 32) return 0;
    for (uint32_t i = 0; i < count; i++) { out[i].id = ids[i]; snprintf(out[i].name, sizeof out[i].name, "%s", names[i] ? names[i] : "unnamed"); }
    return (uint32_t)count;
}

int snap_fsr_sdk_create(SnapFsrSdk *s, const SnapFsrDevice *d, const SnapFsrConfig *c, uint64_t id) {
    if (!s || !c || !c->device_contract_verified || !c->generation || s->context ||
        !c->render_width || !c->render_height || !c->output_width || !c->output_height ||
        c->render_width > c->output_width || c->render_height > c->output_height) return 0;
    SnapFsrProvider providers[32]; uint32_t n = snap_fsr_sdk_query(s, d, providers, 32), found = 0;
    for (uint32_t i = 0; i < n; i++) if (providers[i].id == id) found = 1;
    if (!found) return 0;
    s->config = *c;
    s->override = (struct ffxOverrideVersion){.header.type = FFX_API_DESC_TYPE_OVERRIDE_VERSION, .versionId = id};
    s->version = (struct ffxCreateContextDescUpscaleVersion){.header = {FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE_VERSION, &s->override.header}, .version = FFX_UPSCALER_VERSION};
    s->backend = (struct ffxCreateBackendVKDesc){.header = {FFX_API_CREATE_CONTEXT_DESC_TYPE_BACKEND_VK, &s->version.header}, .deviceContext = {d->device, d->physical_device, d->get_device_proc}};
    s->upscale = (struct ffxCreateContextDescUpscale){.header = {FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE, &s->backend.header},
        .maxRenderSize = {c->render_width, c->render_height}, .maxUpscaleSize = {c->output_width, c->output_height},
        .flags = (c->hdr ? FFX_UPSCALE_ENABLE_HIGH_DYNAMIC_RANGE : 0) | (c->inverted_depth ? FFX_UPSCALE_ENABLE_DEPTH_INVERTED : 0) |
        (c->infinite_depth ? FFX_UPSCALE_ENABLE_DEPTH_INFINITE : 0) | (c->auto_exposure ? FFX_UPSCALE_ENABLE_AUTO_EXPOSURE : 0)};
    if (s->create(&s->context, &s->upscale.header, NULL) != FFX_API_RETURN_OK) {
        if (s->context) s->destroy(&s->context, NULL);
        s->context = NULL; return 0;
    }
    s->fresh = 1; return 1;
}

static uint32_t format(VkFormat f) {
    switch (f) {
    case VK_FORMAT_R32_SFLOAT: case VK_FORMAT_D32_SFLOAT: return FFX_API_SURFACE_FORMAT_R32_FLOAT;
    case VK_FORMAT_R16G16_SFLOAT: return FFX_API_SURFACE_FORMAT_R16G16_FLOAT;
    case VK_FORMAT_R32G32_SFLOAT: return FFX_API_SURFACE_FORMAT_R32G32_FLOAT;
    case VK_FORMAT_R16G16B16A16_SFLOAT: return FFX_API_SURFACE_FORMAT_R16G16B16A16_FLOAT;
    case VK_FORMAT_R8G8B8A8_UNORM: return FFX_API_SURFACE_FORMAT_R8G8B8A8_UNORM;
    case VK_FORMAT_B8G8R8A8_UNORM: return FFX_API_SURFACE_FORMAT_B8G8R8A8_UNORM;
    case VK_FORMAT_R8_UNORM: return FFX_API_SURFACE_FORMAT_R8_UNORM;
    default: return FFX_API_SURFACE_FORMAT_UNKNOWN;
    }
}

static struct FfxApiResource resource(const SnapFsrImage *i, int output) {
    struct FfxApiResource r = {0};
    if (!i->image) return r;
    r.resource = (void *)(uintptr_t)i->image;
    r.state = output ? FFX_API_RESOURCE_STATE_UNORDERED_ACCESS : FFX_API_RESOURCE_STATE_COMPUTE_READ;
    r.description = (struct FfxApiResourceDescription){.type = FFX_API_RESOURCE_TYPE_TEXTURE2D, .format = format(i->format),
        .width = i->width, .height = i->height, .depth = 1, .mipCount = 1,
        .usage = (i->usage & VK_IMAGE_USAGE_STORAGE_BIT ? FFX_API_RESOURCE_USAGE_UAV : 0) |
                 (i->format == VK_FORMAT_D32_SFLOAT ? FFX_API_RESOURCE_USAGE_DEPTHTARGET : 0)};
    return r;
}

int snap_fsr_sdk_dispatch(SnapFsrSdk *s, const SnapFsrFrame *f) {
    if (!s || !s->context || !snap_fsr_sdk_validate(&s->config, f)) return 0;
    struct ffxDispatchDescUpscale q = {.header.type = FFX_API_DISPATCH_DESC_TYPE_UPSCALE,
        .commandList = (void *)f->command_buffer, .color = resource(&f->color, 0), .depth = resource(&f->depth, 0),
        .motionVectors = resource(&f->motion, 0), .exposure = resource(&f->exposure, 0),
        .reactive = resource(&f->reactive, 0), .transparencyAndComposition = resource(&f->transparency, 0), .output = resource(&f->output, 1),
        .jitterOffset = {f->jitter_x, f->jitter_y}, .motionVectorScale = {f->motion_scale_x, f->motion_scale_y},
        .renderSize = {s->config.render_width, s->config.render_height}, .upscaleSize = {s->config.output_width, s->config.output_height},
        .frameTimeDelta = f->delta_ms, .preExposure = f->pre_exposure, .reset = f->reset || s->fresh,
        .cameraNear = f->camera_near, .cameraFar = f->camera_far, .cameraFovAngleVertical = f->vertical_fov, .viewSpaceToMetersFactor = f->meters_factor};
    if (s->dispatch(&s->context, &q.header) != FFX_API_RETURN_OK) { s->fresh = 1; return 0; }
    s->fresh = 0; return 1;
}

int snap_fsr_sdk_memory_usage(SnapFsrSdk *s, uint64_t *total, uint64_t *aliasable) {
    if (total) *total = 0;
    if (aliasable) *aliasable = 0;
    if (!s || !s->context || !total || !aliasable) return 0;
    FfxApiEffectMemoryUsage usage = {0};
    struct ffxQueryDescUpscaleGetGPUMemoryUsage q = {
        .header.type = FFX_API_QUERY_DESC_TYPE_UPSCALE_GPU_MEMORY_USAGE, .gpuMemoryUsageUpscaler = &usage};
    if (s->query(&s->context, &q.header) != FFX_API_RETURN_OK) return 0;
    *total = usage.totalUsageInBytes;
    *aliasable = usage.aliasableUsageInBytes;
    return 1;
}

void snap_fsr_sdk_close(SnapFsrSdk *s) {
    if (!s) return;
    if (s->context) s->destroy(&s->context, NULL);
    if (s->module) FreeLibrary(s->module);
    free(s);
}
#else
struct SnapFsrSdk { int unused; };
SnapFsrSdk *snap_fsr_sdk_open(void) { return NULL; }
uint32_t snap_fsr_sdk_query(SnapFsrSdk *s, const SnapFsrDevice *d, SnapFsrProvider *p, uint32_t n) { (void)s; (void)d; (void)p; (void)n; return 0; }
int snap_fsr_sdk_create(SnapFsrSdk *s, const SnapFsrDevice *d, const SnapFsrConfig *c, uint64_t id) { (void)s; (void)d; (void)c; (void)id; return 0; }
int snap_fsr_sdk_dispatch(SnapFsrSdk *s, const SnapFsrFrame *f) { (void)s; (void)f; return 0; }
int snap_fsr_sdk_memory_usage(SnapFsrSdk *s, uint64_t *total, uint64_t *aliasable) {
    (void)s;
    if (total) *total = 0;
    if (aliasable) *aliasable = 0;
    return 0;
}
void snap_fsr_sdk_close(SnapFsrSdk *s) { (void)s; }
#endif
