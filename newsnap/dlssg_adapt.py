"""FG-DLSS: NVIDIA DLSS frame generation (AC_FRAME_GEN=dlss / frame_gen = dlss), RTX 40 and 50 series.

Raw NGX feature 11 (nvngx_dlssg.dll), as NVIDIA's DLSS-FG Programming Guide describes it: one interpolated frame into
an image of ours, shown by the present thread like the FSR generated frame (framegen_adapt.py). It needs DLSS as the
upscaler (or DLSS Native AA): vk_dlaa.c hands each frame's depth and motion vectors to snap_fsr_fg.c right after the
Super Resolution evaluation, and its NGX core runs the generation (overlays/snap_dlssg.inc, included at its end).
"""


def edits():
    return {
        'runtime/cfg.c': [
            ('{"FRAME_GEN", "off", "off|fsr", RESTART}', '{"FRAME_GEN", "off", "off|fsr|dlss", RESTART}'),
        ],
        'runtime/vk_dlaa.c': [
            # this frame's clip space to the last frame's, for the generation's camera
            ('    memcpy(D.cam_prev, cur_vp, sizeof cur_vp);\n    D.cam_prev_ok = 1;',
             '    {   // FG-DLSS\n'
             '        extern double snap_dlssg_c2p[16];\n'
             '        extern int snap_dlssg_c2p_ok;\n'
             '        snap_dlssg_c2p_ok = have_m;\n'
             '        if (have_m) memcpy(snap_dlssg_c2p, m, sizeof m);\n'
             '    }\n'
             '    memcpy(D.cam_prev, cur_vp, sizeof cur_vp);\n    D.cam_prev_ok = 1;'),
            # NGX is not thread-safe: the generation evaluates on the present thread
            ('        NgxResult r = N.evaluate(cb, e->feat, p, NULL);\n'
             '        if (!NGX_OK(r)) return dl_fail("DLSS evaluation", r), 0;',
             '        void snap_ngx_lock(void);\n'
             '        void snap_ngx_unlock(void);\n'
             '        void snap_fg_prepare_dlss(VkCommandBuffer cb, VkImage depth, VkFormat depth_format, uint32_t level,\n'
             '                                  uint32_t layer, VkImage motion, uint32_t w, uint32_t h, uint32_t ow,\n'
             '                                  uint32_t oh, float jitter_x, float jitter_y, int reset);\n'
             '        snap_ngx_lock();\n'
             '        NgxResult r = N.evaluate(cb, e->feat, p, NULL);\n'
             '        snap_ngx_unlock();\n'
             '        if (!NGX_OK(r)) return dl_fail("DLSS evaluation", r), 0;\n'
             '        full_barrier(cb);\n'
             '        snap_fg_prepare_dlss(cb, z->image, z->format, z->level, z->base_layer, e->mv, w, h, ow, oh, jx, jy,\n'
             '                             D.reset);   // FG-DLSS: this frame\'s depth and motion vectors'),
            ('    vk_xess_release();\n    vk_fsr3_shutdown();\n}\n',
             '    vk_xess_release();\n    vk_fsr3_shutdown();\n}\n\n#include "snap_dlssg.inc"\n'),
        ],
    }
