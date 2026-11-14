"""FG-01: AMD FSR frame generation (off by default; AC_FRAME_GEN=fsr / frame_gen = fsr).

Needs the FSR temporal path (FSR 3.1 or FSR 4, upscaling or Native AA), like frame
generation in other games: its depth, motion vectors and jitter feed the generation
prepare, recorded right after the FSR upscale (snap_fsr_runtime.inc). The present thread
(vk_backend.c) then shows one generated frame halfway to each real frame's display time,
made by the FidelityFX SDK 2.4 Vulkan provider into an image of ours
(newsnap/overlays/snap_fsr_fg.c), not through FFX's own swapchain. Weeping of the Empire
(TotK recomp, engine/runtime/nvn/vulkan/ffx.c) uses frame generation the same way.
"""

PRESENT_BEFORE = '''        vk_present_blit(j.image, VK_IMAGE_LAYOUT_GENERAL, j.format, j.w, j.h, j.has_crop ? j.crop : NULL);
        uint64_t f = vk_sync_submit(NULL, 0);'''

PRESENT_AFTER = '''        uint64_t fg_real_at = 0;
        if (j.fg) {   // FG-01: the generated frame goes out first, halfway between the last real frame and this one
            snap_fg_arm(j.fg);
            vk_present_blit(j.image, VK_IMAGE_LAYOUT_GENERAL, j.format, j.w, j.h, j.has_crop ? j.crop : NULL);
            snap_fg_arm(0);
            uint64_t now = kern_now_ns(), gen_at = now;
            if (j.at && last && j.at > last) gen_at = last + (j.at - last) / 2;
            else if (fg_interval) fg_real_at = now + fg_interval / 2;   // no pacer target: half the measured interval later
            wait_until(gen_at);
            vk_present_flip();
        }
        vk_present_blit(j.image, VK_IMAGE_LAYOUT_GENERAL, j.format, j.w, j.h, j.has_crop ? j.crop : NULL);
        uint64_t f = vk_sync_submit(NULL, 0);'''


def edits():
    return {
        'runtime/cfg.c': [
            ('"FPS", "FREEZE_IDLE",', '"FPS", "FRAME_GEN", "FREEZE_IDLE",'),
            ('    {"FPS", "frame rate"},', '    {"FPS", "frame rate"}, {"FRAME_GEN", "display"},'),
            ('{"FOV", "100", "70..140", LIVE},', '{"FOV", "100", "70..140", LIVE}, {"FRAME_GEN", "off", "off|fsr", RESTART},'),
        ],
        'runtime/vk_dlaa.c': [
            ('    memcpy(D.proj, pj, sizeof D.proj), D.proj_ok = 1;',
             '    memcpy(D.proj, pj, sizeof D.proj), D.proj_ok = 1;\n'
             '    { extern float snap_fg_view[16]; memcpy(snap_fg_view, vw, sizeof snap_fg_view); }   // FG-01 camera'),
        ],
        'runtime/vk_backend.c': [
            ('#include "vk_dlaa.h"', '#include "vk_dlaa.h"\n#include "snap_fsr_fg.h"'),
            ('    uint64_t frame, at, queued, value;', '    uint64_t frame, at, queued, value;\n    uint64_t fg;            // FG-01: the frame generation prepare of this frame, 0 for none'),
            ('    uint64_t last = 0, last_queued = 0;', '    uint64_t last = 0, last_queued = 0, fg_interval = 0;'),
            (PRESENT_BEFORE, PRESENT_AFTER),
            ('        wait_until(j.at);\n        uint64_t t1 = kern_now_ns();',
             '        wait_until(j.at ? j.at : fg_real_at);\n        uint64_t t1 = kern_now_ns();\n'
             '        if (last && t1 > last && t1 - last < 100000000) fg_interval = t1 - last;'),
            ('    vk_hdr_present_source(img, &j.scene, &j.scene_format);',
             '    j.fg = snap_fg_take();   // FG-01: taken here, in order with the replay\n'
             '    vk_hdr_present_source(img, &j.scene, &j.scene_format);'),
        ],
        'runtime/gfx_present.c': [
            ('#include "ui/menu.h"\n#include "vk.h"', '#include "ui/menu.h"\n#include "vk.h"\n#include "snap_fsr_fg.h"'),
            ('    vkBeginCommandBuffer(cb, &bi);\n    uint64_t crumb = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);',
             '    vkBeginCommandBuffer(cb, &bi);\n'
             '    if (general) {   // FG-01: an armed present shows the generated frame made from this picture\n'
             '        VkImage generated = snap_fg_present_source(cb, src, fmt, w, h);\n'
             '        if (generated) src = generated;\n'
             '    }\n'
             '    uint64_t crumb = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);'),
            ('        vk_fsr_release();\n        vk_color_release();', '        vk_fsr_release();\n        snap_fg_release();\n        vk_color_release();'),
        ],
    }
