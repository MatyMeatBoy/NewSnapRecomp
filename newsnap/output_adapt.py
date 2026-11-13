"""Exact source seams for the experimental Snap DISPLAY-only output bridge."""


def edits():
    """Stage these beside the engine resize patch; does not mutate the donor."""
    return {
        'runtime/vk_texture.c': [
            ('        if (r != VK_SUCCESS) {\n            log_limited(&n_failed, "image creation failed',
             '        if (r != VK_SUCCESS) {\n            if (output_scale > 1.0f) rt_fatal("snap supersampling allocation failed: %ux%u (Vulkan %d); select render scale 100 or lower and restart", w, h, (int)r);\n            log_limited(&n_failed, "image creation failed'),
            ('"vk: shadow map %ux%u fmt %#x made %ux%u (AC_SHADOW_SCALE): %.1f MiB of its own"',
             '"vk: enlarged render image %ux%u fmt %#x made %ux%u: %.1f MiB of its own"'),
            ('#include "vk_exec.h"', '#include "vk_exec.h"\n#include "snap_output_scale.h"'),
            ('    float scale = (float)shadow;', '''    float scale = (float)shadow;
    float output_scale = snap_output_image_scale(d, samples,
        f.vk == f.ideal && !f.depth && !f.stencil && !f.expand_rgb && !f.astc_bw,
        c->props.limits.maxImageDimension2D);
    if (output_scale > 1.0f) scale = output_scale; // DISPLAY only; engine scene targets are untouched'''),
        ],
        'runtime/vk_exec.c': [
            ('#include "vk_exec.h"', '#include "vk_exec.h"\n#include "snap_output_scale.h"'),
            ('    o->scale = img->scale > 0 ? img->scale : 1.0f;',
             '    o->scale = snap_output_target_scale(&t->d, img->samples, img->scale);'),
        ],
    }
