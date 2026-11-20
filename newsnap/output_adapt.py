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
            # Snap's shadow maps (SS-03): every square depth map of 256 to 2048 texels, 2D or array, one level.
            # The sun map is DEPTH32F 1024x1024 (SS-02 trace); the scene's depth is 16:9 and never square.
            # AC_SHADOW_SCALE (1..4 or auto) enlarges them like the donor's maps.
            ('    if (!sun && !cascades) return 1;',
             '    int snap_sun = snap_shadow_map_class(d);'+'\n'+
             '    if (!sun && !cascades && !snap_sun) return 1;'),
            ('        int s = cfg_int("AC_SHADOW_SCALE");', '        int s = snap_shadow_scale_parse(cfg_value("AC_SHADOW_SCALE"));'),
            ('    float scale = (float)shadow;', '''    float scale = (float)shadow;
    float output_scale = snap_output_image_scale_ex(d, samples,
        (f.depth || f.stencil) ? 1 : (f.vk == f.ideal && !f.expand_rgb && !f.astc_bw),
        c->props.limits.maxImageDimension2D, tex_mirrored(t), f.depth || f.stencil);
    if (output_scale > 1.0f) scale = output_scale; // docked full-screen render targets only (SS-02)'''),
            ('                const uint8_t *src = tmp + (size_t)z * g2.img + (size_t)ey * g2.row;\n                uint8_t *dst = mem + (size_t)z * g->img + (size_t)y * g->row;\n                for (int32_t x = 0; x < r->width; x++) memcpy(dst + (size_t)x * bpb, src + xs[x] * bpb, bpb);',
             '                const uint8_t *src = tmp + (size_t)z * g2.img + (size_t)ey * g2.row;\n                uint8_t *dst = mem + (size_t)z * g->img + (size_t)y * g->row;\n                if (snap_box_read((int)e->f.vk, bpb)) {   // SS-03: 8-bit colour averages the texels each game texel covers\n                    int32_t ya = (int32_t)floorf((float)(r->yoffset + y) * k) - y0, yb = (int32_t)ceilf((float)(r->yoffset + y + 1) * k) - y0;\n                    ya = ya < 0 ? 0 : ya; yb = yb > (int32_t)h2 ? (int32_t)h2 : yb; if (yb <= ya) yb = ya + 1;\n                    for (int32_t x = 0; x < r->width; x++) {\n                        int32_t xa = (int32_t)floorf((float)(r->xoffset + x) * k) - x0, xb = (int32_t)ceilf((float)(r->xoffset + x + 1) * k) - x0;\n                        xa = xa < 0 ? 0 : xa; xb = xb > (int32_t)w2 ? (int32_t)w2 : xb; if (xb <= xa) xb = xa + 1;\n                        uint32_t sum[4] = {0, 0, 0, 0}, n = 0;\n                        for (int32_t yy = ya; yy < yb; yy++)\n                            for (int32_t xx = xa; xx < xb; xx++, n++) {\n                                const uint8_t *p = tmp + (size_t)z * g2.img + (size_t)yy * g2.row + (size_t)xx * 4;\n                                sum[0] += p[0], sum[1] += p[1], sum[2] += p[2], sum[3] += p[3];\n                            }\n                        for (int c = 0; c < 4; c++) dst[(size_t)x * 4 + c] = (uint8_t)((sum[c] + n / 2) / n);\n                    }\n                    continue;\n                }\n                for (int32_t x = 0; x < r->width; x++) memcpy(dst + (size_t)x * bpb, src + xs[x] * bpb, bpb);'),
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
             '    int skip = vk_tex_mip_skip() > 0;\n    if (!skip && !snap_hd_photo_scale_on() && snap_host_scale_factor() <= 1.0f) return;'),
        ],
    }
