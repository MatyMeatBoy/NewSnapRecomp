"""ULTRAWIDE-01: AC_ASPECT=ultrawide stretches the 16:9 picture and widens 16:9 cameras (snap_wide.c)."""


def edits():
    return {
        'runtime/cpu.h': [
            ('typedef void (*GuestFn)(Cpu *);', 'void snap_wide_proj_s1(Cpu *c);\ntypedef void (*GuestFn)(Cpu *);'),
        ],
        'runtime/cfg.c': [
            ('{"ASPECT", "fit", "fit|stretch", LIVE}', '{"ASPECT", "fit", "fit|stretch|ultrawide", LIVE}'),
        ],
        'runtime/vk_exec.c': [
            ('#include "snap_hd_photo.h"', '#include "snap_hd_photo.h"\n#include "snap_wide.h"'),
            ('snap_fg_hudless_pass(ex->cb, ex->color[0].img, ex->color[0].format);   // SS-03, FG-02',
             'snap_fg_hudless_pass(ex->cb, ex->color[0].img, ex->color[0].format);   // SS-03, FG-02\n'
             '    if (snap_wide_pass(ex->cb, ex->pass_ncolor && ex->color[0].image ? ex->color[0].img : NULL, ex->color[0].format))\n'
             '        ex->dirty |= VK_EXEC_DIRTY_VIEWPORT | VK_EXEC_DIRTY_SCISSOR;   // ULTRAWIDE-01'),
        ],
        'runtime/vk_exec_draw.c': [
            ('#include "snap_hd_photo.h"', '#include "snap_hd_photo.h"\n#include "snap_wide.h"'),
            ('    vk_dlaa_viewport(ex, &v);   // the scene\'s draws move by the DLAA jitter',
             '    vk_dlaa_viewport(ex, &v);   // the scene\'s draws move by the DLAA jitter\n'
             '    snap_wide_viewport(ex->pass_w, &v);   // ULTRAWIDE-01: the interface in the middle 16:9'),
            ('        VkRect2D r = vk_exec_scissor(ex);\n        vkCmdSetScissorWithCount(cb, 1, &r);',
             '        VkRect2D r = vk_exec_scissor(ex);\n        snap_wide_scissor(ex->pass_w, &r);\n        vkCmdSetScissorWithCount(cb, 1, &r);'),
            ('    int td_on = td_mode();\n',
             '    int td_on = td_mode();\n    if (snap_wide_capture()) td_on = 0;   // ULTRAWIDE-01: photo capture passes resolve every binding\n'),
            ('        if (img && !storage) view = snap_hd_photo_view(img->image, view);',
             '        if (img && !storage) view = snap_hd_photo_view(img->image, view);\n'
             '        if (img && !storage) view = snap_wide_capture_view(img->image, view);   // ULTRAWIDE-01: the 16:9 scene'),
        ],
        'runtime/host.h': [
            ('void res_wide_window(unsigned w, unsigned h);',
             'void res_wide_window(unsigned w, unsigned h);\nvoid snap_wide_window(unsigned w, unsigned h);\nint snap_aspect_fills(const char *aspect);'),
        ],
        'runtime/gfx_present.c': [
            ('!strcmp(cfg_value("AC_ASPECT"), "stretch")) return;', 'snap_aspect_fills(cfg_value("AC_ASPECT"))) return;'),
            ('    res_wide_window(ext.width, ext.height);', '    res_wide_window(ext.width, ext.height);\n    snap_wide_window(ext.width, ext.height);'),
        ],
    }
