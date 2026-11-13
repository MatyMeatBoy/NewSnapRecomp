// Experimental bridge for Snap's native-size DISPLAY textures only.
// The engine already emits enlarged output coordinates; raster scale stays 1.
#pragma once
#include <stdint.h>
#include <string.h>
#include "nvn_obj.h"
#include "cfg.h"
#include "ov.h"

static inline int snap_output_display_class(const nvn_texdesc *d, uint32_t samples) {
    const uint32_t allowed = NVN_TEXTURE_FLAGS_DISPLAY | NVN_TEXTURE_FLAGS_COMPRESSIBLE;
    if (!(d->flags & NVN_TEXTURE_FLAGS_DISPLAY) || ((uint32_t)d->flags & ~allowed) ||
        d->target != NVN_TEXTURE_TARGET_2D || d->width != 1920 || d->height != 1080 ||
        d->depth < 0 || d->depth > 1 || d->levels != 1 || samples != 1 || d->samples < 0 || d->samples > 1)
        return 0;
    return d->format == NVN_FORMAT_RGBA8 || d->format == NVN_FORMAT_RGBA8_SRGB ||
           d->format == NVN_FORMAT_BGRA8 || d->format == NVN_FORMAT_BGRA8_SRGB;
}

static inline float snap_output_image_scale(const nvn_texdesc *d, uint32_t samples,
                                             int format_usable, uint32_t max_dimension) {
    if (!format_usable || !snap_output_display_class(d, samples) || ov_handheld()) return 1.0f;
    const char *choice = cfg_value("AC_RENDER_SCALE");
    float scale = choice && !strcmp(choice, "125") ? 1.25f :
                  choice && !strcmp(choice, "150") ? 1.5f :
                  choice && !strcmp(choice, "200") ? 2.0f : 1.0f;
    if (d->width * scale > max_dimension || d->height * scale > max_dimension) return 1.0f;
    return scale;
}

static inline float snap_output_target_scale(const nvn_texdesc *d, uint32_t samples, float image_scale) {
    // pub.scale remains enlarged for logical CPU reads and presentation crop.
    // Only the raster pass sees scale 1: its viewport already comes from the
    // supersampled engine dimensions. All ordinary/shadow scales are preserved.
    if (image_scale > 1.0f && snap_output_display_class(d, samples)) return 1.0f;
    return image_scale > 0 ? image_scale : 1.0f;
}
