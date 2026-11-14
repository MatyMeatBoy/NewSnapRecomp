// Snap internal resolution above 100 % (SS-02): host-side scaling of the game's
// full-screen render targets, the way emulators scale resolution.
//
// The game keeps rendering at its own 1920x1080 (docked). Each 2D render
// target of exactly that size (DISPLAY, COMPRESSIBLE or depth/stencil, not
// written by the CPU, not a storage image) is made S times larger on the host.
// The runtime's existing scaled-image path does the rest, as it does for the
// enlarged shadow maps: viewports and scissors of passes into these targets are
// scaled (vk_exec.c pass_scale), gl_FragCoord, integer texel fetches and size
// queries go through the translator's render scale (vk_exec_draw.c
// support_scales), copies scale their regions (vk_exec_xfer.c), CPU reads see
// the game's size, and the presenter shows the larger DISPLAY image.
// The HUD is drawn into the larger DISPLAY target and gains detail too.
// Photo targets (1080x720 and smaller) keep their size, so photos are taken
// from the larger scene with the game's own downscaling draw.
//
// AC_SS_MODE=engine restores the 0.2 experiment (engine resize plus a larger
// DISPLAY image only), kept for comparison; it crops the HUD and the photos.
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "nvn_obj.h"
#include "cfg.h"
#include "ov.h"
#include "host.h"

static inline int snap_ss_engine_mode(void) {
    const char *mode = cfg_get("AC_SS_MODE");
    return mode && !strcmp(mode, "engine");
}

int gfx_display_height(void);                 // gfx_window_win.c: the monitor's height in pixels
int gfx_cfg_fullscreen(void);                 // gfx_present.c
void gfx_cfg_window_size(int *w, int *h);     // gfx_present.c

// AC_RENDER_SCALE above 100: a percentage (125..300), or display: the scale
// that renders the game's 1920x1080 at the height it is shown at (the monitor
// in full screen, the window size otherwise), from 1 to 3.
static inline float snap_ss_parse(const char *choice) {
    if (!choice) return 1.0f;
    if (!strcmp(choice, "display")) {
        int w = 0, h = 0;
        if (gfx_cfg_fullscreen()) h = gfx_display_height();
        else gfx_cfg_window_size(&w, &h);
        float s = h > 0 ? (float)h / 1080.0f : 1.0f;
        return s < 1.0f ? 1.0f : s > 3.0f ? 3.0f : s;
    }
    static const struct { const char *name; float scale; } table[] = {
        {"125", 1.25f}, {"133", 4.0f / 3.0f}, {"150", 1.5f}, {"175", 1.75f},
        {"200", 2.0f}, {"250", 2.5f}, {"300", 3.0f}};
    for (unsigned i = 0; i < sizeof table / sizeof table[0]; i++)
        if (!strcmp(choice, table[i].name)) return table[i].scale;
    return 1.0f;
}

static inline float snap_ss_choice(void) { return snap_ss_parse(cfg_value("AC_RENDER_SCALE")); }

// The host scale in force for docked full-screen targets, 1 when off.
static inline float snap_host_scale_factor(void) {
    if (snap_ss_engine_mode() || ov_handheld() || strcmp(cfg_upscaling(), "off")) return 1.0f;
    return snap_ss_choice();
}

static inline int snap_output_display_class(const nvn_texdesc *d, uint32_t samples) {
    const uint32_t allowed = NVN_TEXTURE_FLAGS_DISPLAY | NVN_TEXTURE_FLAGS_COMPRESSIBLE;
    if (!(d->flags & NVN_TEXTURE_FLAGS_DISPLAY) || ((uint32_t)d->flags & ~allowed) ||
        d->target != NVN_TEXTURE_TARGET_2D || d->width != 1920 || d->height != 1080 ||
        d->depth < 0 || d->depth > 1 || d->levels != 1 || samples != 1 || d->samples < 0 || d->samples > 1)
        return 0;
    return d->format == NVN_FORMAT_RGBA8 || d->format == NVN_FORMAT_RGBA8_SRGB ||
           d->format == NVN_FORMAT_BGRA8 || d->format == NVN_FORMAT_BGRA8_SRGB;
}

// A full-screen (or 16:9 effect) render target of the docked game: what host scaling enlarges.
static inline int snap_host_scale_class(const nvn_texdesc *d, uint32_t samples, int mirrored, int depth_format) {
    const uint32_t refused = NVN_TEXTURE_FLAGS_VIDEO_DECODE | NVN_TEXTURE_FLAGS_IMAGE | NVN_TEXTURE_FLAGS_LINEAR |
                             NVN_TEXTURE_FLAGS_SPARSE | NVN_TEXTURE_FLAGS_LINEAR_RENDER_TARGET;
    if (mirrored || samples != 1 || d->samples > 1 || d->target != NVN_TEXTURE_TARGET_2D) return 0;
    if (d->depth > 1) return 0;
    // The full-screen size, and (AC_SS_CHAIN, on by default) the game's smaller
    // exact-16:9 targets down to 192x108: half-resolution effects, bloom
    // pyramid, luminance. Witch Time scales the same class; storage images and
    // CPU-written textures stay native (refused above and below).
    int full = d->width == 1920 && d->height == 1080;
    int chain = d->width >= 192 && d->width < 1920 && d->width * 9 == d->height * 16;
    if (chain) {
        const char *knob = cfg_get("AC_SS_CHAIN");
        if (knob && !strcmp(knob, "0")) chain = 0;
    }
    // AC_SS_PHOTO=1 (experiment, off): the photo targets too (1080x720 photo, 360x240 and
    // 240x200 thumbnails), plain 8-bit/half colour only (never the BC1 thumbnail target). CPU
    // reads of them average the covered texels (snap_box_read), so saved photos keep their size.
    if (!full && !chain) {
        const char *photo = cfg_get("AC_SS_PHOTO");
        int size = (d->width == 1080 && d->height == 720) || (d->width == 360 && d->height == 240) ||
                   (d->width == 240 && d->height == 200);
        int colour = d->format == NVN_FORMAT_RGBA8 || d->format == NVN_FORMAT_RGBA8_SRGB || d->format == NVN_FORMAT_BGRA8 ||
                     d->format == NVN_FORMAT_BGRA8_SRGB || d->format == NVN_FORMAT_RGBA16F;
        if (!(photo && !strcmp(photo, "1") && size && colour && !depth_format)) return 0;
    }
    if ((uint32_t)d->flags & refused) return 0;
    return (d->flags & (NVN_TEXTURE_FLAGS_DISPLAY | NVN_TEXTURE_FLAGS_COMPRESSIBLE)) || depth_format;
}

// SS-03 shadows: every square depth map (Snap's sun map is DEPTH32F 1024x1024; others
// may be 16/24-bit or arrays), so the shadow option enlarges all of them. The scene's
// own depth is 16:9 and never square.
static inline int snap_shadow_map_class(const nvn_texdesc *d) {
    int depth = d->format == NVN_FORMAT_DEPTH16 || d->format == NVN_FORMAT_DEPTH24 ||
                d->format == NVN_FORMAT_DEPTH24_STENCIL8 || d->format == NVN_FORMAT_DEPTH32F ||
                d->format == NVN_FORMAT_DEPTH32F_STENCIL8;
    int target = d->target == NVN_TEXTURE_TARGET_2D || d->target == NVN_TEXTURE_TARGET_2D_ARRAY;
    return depth && target && d->width == d->height && d->width >= 256 && d->width <= 2048 && d->levels <= 1;
}

// AC_SHADOW_SCALE: 1..4, or "auto": shadow texels follow the 3D resolution, twice the
// scene scale rounded up (1080p 2x, 125-150 % 3x, 200 % and above 4x).
static inline int snap_shadow_scale_parse(const char *v) {
    if (v && !strcmp(v, "auto")) {
        float r = snap_host_scale_factor();
        int s = (int)(2.0f * r + 0.999f);
        return s < 2 ? 2 : s > 4 ? 4 : s;
    }
    int s = v ? atoi(v) : 1;
    return s < 1 ? 1 : s > 4 ? 4 : s;
}

// SS-03 (AC_HD_PHOTOS, on by default): the 360x240 RGBA8 picture each photo
// thumbnail is encoded from is drawn 3x larger, 1080x720 like the photo itself,
// at every internal resolution. snap_hd_photo.c keeps a copy for the thumbnail.
static inline int snap_hd_photo_scale_on(void) {
    const char *v = cfg_get("AC_HD_PHOTOS");
    return !(v && !strcmp(v, "0"));
}

static inline float snap_hd_photo_scale(const nvn_texdesc *d, uint32_t samples, int mirrored, int depth_format) {
    const uint32_t refused = NVN_TEXTURE_FLAGS_VIDEO_DECODE | NVN_TEXTURE_FLAGS_IMAGE | NVN_TEXTURE_FLAGS_LINEAR |
                             NVN_TEXTURE_FLAGS_SPARSE | NVN_TEXTURE_FLAGS_LINEAR_RENDER_TARGET;
    if (!snap_hd_photo_scale_on() || mirrored || depth_format || samples != 1 || d->samples > 1) return 1.0f;
    if (d->target != NVN_TEXTURE_TARGET_2D || d->depth > 1 || d->width != 360 || d->height != 240) return 1.0f;
    if (d->format != NVN_FORMAT_RGBA8 || ((uint32_t)d->flags & refused)) return 1.0f;
    return 3.0f;
}

// format_usable: a colour format stored as the game's (no expansion or ASTC
// conversion), or any depth/stencil format.
static inline float snap_output_image_scale_ex(const nvn_texdesc *d, uint32_t samples, int format_usable,
                                               uint32_t max_dimension, int mirrored, int depth_format) {
    if (!format_usable) return 1.0f;
    float hd = snap_hd_photo_scale(d, samples, mirrored, depth_format);
    if (hd > 1.0f) return d->width * hd <= max_dimension && d->height * hd <= max_dimension ? hd : 1.0f;
    if (ov_handheld()) return 1.0f;
    float scale;
    int take;
    if (snap_ss_engine_mode()) {
        scale = snap_ss_choice();
        take = snap_output_display_class(d, samples);
    } else {
        scale = snap_host_scale_factor();
        take = scale > 1.0f && snap_host_scale_class(d, samples, mirrored, depth_format);
    }
    const char *trace = getenv("NEWSNAP_HOST_SCALE_TRACE");
    static int traced;
    // Every render-target-like texture (full-screen, compressible or depth), to map the
    // game's render graph: 16:9 chains, shadow maps.
    if (trace && !strcmp(trace, "1") && traced < 256 &&
        ((d->width == 1920 && d->height == 1080) || (d->flags & NVN_TEXTURE_FLAGS_COMPRESSIBLE) || depth_format)) {
        traced++;
        rt_log("snap host scale: %dx%dx%d target %d fmt %#x flags %#x levels %d samples %u mirrored %d usable %d -> %s",
               (int)d->width, (int)d->height, (int)d->depth, (int)d->target, (unsigned)d->format, (unsigned)d->flags,
               (int)d->levels, samples, mirrored, format_usable, take && scale > 1.0f ? "scaled" : "kept");
    }
    if (!take || scale <= 1.0f) return 1.0f;
    if (d->width * scale > max_dimension || d->height * scale > max_dimension) return 1.0f;
    return scale;
}

// Kept for the 0.2 call shape (tests and AC_SS_MODE=engine).
static inline float snap_output_image_scale(const nvn_texdesc *d, uint32_t samples,
                                             int format_usable, uint32_t max_dimension) {
    return snap_output_image_scale_ex(d, samples, format_usable, max_dimension, 0, 0);
}

static inline float snap_output_target_scale(const nvn_texdesc *d, uint32_t samples, float image_scale) {
    // Engine mode: the engine already emits enlarged coordinates for the
    // DISPLAY pass, so its raster scale stays 1. Host mode: the game draws at
    // its own size and every enlarged target scales its passes.
    if (snap_ss_engine_mode() && image_scale > 1.0f && snap_output_display_class(d, samples)) return 1.0f;
    return image_scale > 0 ? image_scale : 1.0f;
}

// SS-03: CPU reads of an enlarged 8-bit RGBA/BGRA texture average the texels each of the
// game's texels covers (vk_texture.c image_texels), instead of taking the nearest one.
// (VkFormat values: R8G8B8A8_UNORM 37, _SRGB 43, B8G8R8A8_UNORM 44, _SRGB 50; plain ints keep
// this header free of the Vulkan headers for its native test.)
static inline int snap_box_read(int vk_format, size_t bpb) {
    return bpb == 4 && (vk_format == 37 || vk_format == 43 || vk_format == 44 || vk_format == 50);
}
