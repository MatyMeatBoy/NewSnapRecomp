"""Exact source seams for Snap's internal resolution above 100 % (SS-02).

Host mode (default): docked 1920x1080 render targets are enlarged on the host
and the runtime's scaled-image path handles viewports, fragment coordinates,
texel fetches, copies and CPU reads. AC_SS_MODE=engine keeps the 0.2
DISPLAY-only bridge for comparison. See newsnap/overlays/snap_output_scale.h.
"""


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
    float output_scale = snap_output_image_scale_ex(d, samples,
        (f.depth || f.stencil) ? 1 : (f.vk == f.ideal && !f.expand_rgb && !f.astc_bw),
        c->props.limits.maxImageDimension2D, tex_mirrored(t), f.depth || f.stencil);
    if (output_scale > 1.0f) scale = output_scale; // docked full-screen render targets only (SS-02)'''),
        ],
        'runtime/vk_exec.c': [
            ('#include "vk_exec.h"', '#include "vk_exec.h"\n#include "snap_output_scale.h"'),
            ('    o->scale = img->scale > 0 ? img->scale : 1.0f;',
             '    o->scale = snap_output_target_scale(&t->d, img->samples, img->scale);'),
        ],
        'runtime/vk_exec_draw.c': [
            ('#include "vk_exec.h"', '#include "vk_exec.h"\n#include "snap_output_scale.h"'),
            # Fragment coordinates, texel fetches and size queries of enlarged
            # targets need the translator's render scale, not only with mip skip.
            ('    int skip = vk_tex_mip_skip() > 0;\n    if (!skip) return;',
             '    int skip = vk_tex_mip_skip() > 0;\n    if (!skip && snap_host_scale_factor() <= 1.0f) return;'),
        ],
    }
