"""Snap-specific scene/camera seams for the donor's portable temporal machinery."""


def edits():
    return {'runtime/resolution.c': [
        ('#include "cfg.h"', '#include "cfg.h"\n#define NEWSNAP_TEMPORAL_CONFIG\n#include "snap_temporal.h"'),
        ('void res_game_size(unsigned out[2]) {',
         'void res_game_size(unsigned out[2]) { snap_temporal_output(out); return;'),
        ('void res_scene_size(unsigned out[2]) {',
         'void res_scene_size(unsigned out[2]) { snap_temporal_output(out); unsigned scale=snap_temporal_percent(); out[0]=out[0]*scale/100; out[1]=out[1]*scale/100; return;'),
        ('int res_scene_reduced(void) { return S.reduced; }',
         'int res_scene_reduced(void) { return snap_temporal_percent()<100; }'),
    ], 'runtime/vk_dlaa.c': [
        ('static int pick(void) {', 'static int pick(void) {\n    if (!strcmp(cfg_upscaling(), "off")) return BK_NONE;'),
        ('#include "vk_fsr3.h"', '#include "vk_fsr3.h"\n#define NEWSNAP_TEMPORAL_CONFIG\n#include "snap_temporal.h"'),
        ('b->size == CAM_BYTES && b->addr', 'b->size == 0x2e8 && b->addr'),
        ('''        if (!vk_usnap_copy(b->addr, CAM_BYTES, c->block))   // no snapshot (AC_UBO_SNAPSHOT=0): guest memory
            memcpy(c->block, (const void *)(uintptr_t)b->addr, CAM_BYTES);''',
         '''        float raw[0x2e8 / sizeof(float)];
        if (!vk_usnap_copy(b->addr, sizeof raw, raw))
            memcpy(raw, (const void *)(uintptr_t)b->addr, sizeof raw);
        if (!snap_camera_decode(raw, sizeof raw, c->block)) { c->have = 0; return; }'''),
        ('(1 << 1) | (hdr ? (1 << 0) | (1 << 6) : 0)',
         '(1 << 1) | (1 << 3) | (hdr ? (1 << 0) | (1 << 6) : 0)'),
        ('int hdr = !up || vk_hdr_wanted();',
         'int hdr = 1; // Snap HDR composite remains linear until the final RGBA8 tone-map pass.'),
        # Snap's last full-resolution HDR pass precedes the RGBA8 output pass;
        # both bloom and tone mapping update this image in place, without depth.
        ('D.resolved = 1;   // SMAA\'s edges and weights, which come first, are skipped for the upscaler',
         'D.comp = D.color, D.comp_ok = 1;\n        D.resolved = 1; // Snap composite remains the full scene image'),
        ('return res_scene_reduced() && c->width == s[0] && c->height == s[1];',
         'uint32_t o[2]; game_size(o);\n    return c->width < o[0] && c->height < o[1];'),
        ('if (D.gbuf && !D.ended && ex->pass_ncolor == 1',
         'unsigned expected_scene[2]; res_scene_size(expected_scene);\n    if (c->width == expected_scene[0] && c->height == expected_scene[1] && D.gbuf && !D.ended && ex->pass_ncolor == 1'),
        ('const VkExecTarget *t = &D.color, *z = &D.depth;',
         'const VkExecTarget *t = &D.color, *z = &D.depth;\n    uint64_t verified_camera; if (!frame_camera(&verified_camera)) return 0;'),
    ], 'runtime/vk_mvprev.c': [
        ('b != 3 && n >= 48', 'b != 3 && n >= 64'),
        ('(ab < 0 || b == 14)', '(ab < 0 || b == 4)'),
        ('o->anchor[0] = m[3], o->anchor[1] = m[7], o->anchor[2] = m[11]',
         'o->anchor[0] = m[12], o->anchor[1] = m[13], o->anchor[2] = m[14]'),
    ]}
