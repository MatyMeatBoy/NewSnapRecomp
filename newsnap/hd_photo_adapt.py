"""SS-03: photo thumbnails (in-level preview, folder and selection screens) from a 1080x720 copy.

See newsnap/overlays/snap_hd_photo.c. The 360x240 RGBA8 picture Snap encodes to BC1 is drawn
3x larger (snap_output_scale.h snap_hd_photo_scale); the pass that encodes a 360x240 BC texture
first copies that picture to an image kept for the BC texture, and sampling the BC texture binds
the copy. No per-vendor branch: the BC texture is matched by format and size, whether it is drawn
through block views or vk_exec.c's stand-in.
"""


def edits():
    return {
        'runtime/cfg.c': [
            ('"FPS", "FRAME_GEN", "FREEZE_IDLE",', '"FPS", "FRAME_GEN", "FREEZE_IDLE", "HD_PHOTOS",'),
            ('{"FRAME_GEN", "display"},', '{"FRAME_GEN", "display"}, {"HD_PHOTOS", "display"},'),
            ('{"FRAME_GEN", "off", "off|fsr", RESTART},', '{"FRAME_GEN", "off", "off|fsr", RESTART}, {"HD_PHOTOS", "1", "0|1", RESTART},'),
            ('{"SHADOW_SCALE", "1", "1..4", RESTART}', '{"SHADOW_SCALE", "auto", "1|2|3|4|auto", RESTART}'),
        ],
        'runtime/vk_exec.c': [
            ('#include "snap_output_scale.h"', '#include "snap_output_scale.h"\n#include "snap_hd_photo.h"'),
            ('    vkCmdBeginRendering(ex->cb, &ri);\n    vk_exec_frame.passes++;',
             '    if (ex->pass_ncolor && ex->color[0].image) snap_hd_photo_pass(ex->cb, ex->color[0].img), snap_fg_hudless_pass(ex->cb, ex->color[0].img, ex->color[0].format);   // SS-03, FG-02\n'
             '    vkCmdBeginRendering(ex->cb, &ri);\n    vk_exec_frame.passes++;'),
        ],
        'runtime/vk_exec_draw.c': [
            ('#include "snap_output_scale.h"', '#include "snap_output_scale.h"\n#include "snap_hd_photo.h"'),
            ('        if (img) view = get_view(ex, img, &v, hv, r->type, storage), *image = img->image;',
             '        if (img) view = get_view(ex, img, &v, hv, r->type, storage), *image = img->image;\n'
             '        if (img && !storage) view = snap_hd_photo_view(img->image, view);   // SS-03: a thumbnail\'s 1080x720 copy'),
            ('ep = vk_texture_epoch(), sg = vk_sampler_gen();',
             'ep = vk_texture_epoch(), sg = vk_sampler_gen() + snap_hd_photo_gen();'),
            ('    vk_exec_bc_gone(image);\n    vk_hdr_image_gone(image);',
             '    vk_exec_bc_gone(image);\n    snap_hd_photo_gone(image);\n    vk_hdr_image_gone(image);'),
        ],
        'runtime/vk_texture.c': [
            ('    e->wt_n = 0;\n', '    e->wt_n = 0;\n    { void snap_hd_photo_gone(VkImage bc); snap_hd_photo_gone(e->pub.image); }   // SS-03: CPU content replaces a thumbnail\'s copy\n'),
        ],
    }
