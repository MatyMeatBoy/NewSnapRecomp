"""TEXPACK-01: HD texture packs by content hash (newsnap/overlays/snap_texpack.c).

Dolphin's custom textures, applied to the replay: vk_texture.c upload hashes each texture the game wrote, dumps it
(NEWSNAP_TEX_DUMP) or attaches the pack's <hash>.dds; get_view makes the sampled views on the HD image with the game
view's channel mapping; the HD image goes with the game's (vk_exec_image_gone).
"""


def edits():
    return {
        'runtime/cfg.c': [
            ('"FPS", "FRAME_GEN", "FREEZE_IDLE", "HD_PHOTOS",', '"FPS", "FRAME_GEN", "FREEZE_IDLE", "HD_PHOTOS", "HD_SHADOWS", "TEX_PACK", "TEX_PACK_SAVE",'),
            ('{"HD_PHOTOS", "display"},', '{"HD_PHOTOS", "display"}, {"HD_SHADOWS", "display"}, {"TEX_PACK", "display"}, {"TEX_PACK_SAVE", "display"},'),
            ('{"HD_PHOTOS", "1", "0|1", RESTART},', '{"HD_PHOTOS", "1", "0|1", RESTART}, {"HD_SHADOWS", "0", "0|1", RESTART}, {"TEX_PACK", "1", "0|1", RESTART}, {"TEX_PACK_SAVE", "0", "0|1", RESTART},'),
        ],
        'runtime/vk_texture.c': [
            ('    e->n_up++;\n    perf_end(PERF_TEX, p0);\n}',
             '    e->n_up++;\n'
             '    if (e->uploaded) {   // TEXPACK-01: hash, dump, HD image\n'
             '        void snap_texpack_uploaded(const VkTexImage *img, const void *mem, uint64_t size, int nvn_format);\n'
             '        snap_texpack_uploaded(&e->pub, t->mem, t->L.size, (int)d->format);\n'
             '    }\n'
             '    perf_end(PERF_TEX, p0);\n}'),
        ],
        'runtime/vk_exec_draw.c': [
            ('#include "snap_wide.h"', '#include "snap_wide.h"\n'
             'VkImage snap_texpack_image(VkImage game, VkFormat *fmt, uint32_t *levels);\n'
             'void snap_texpack_gone(VkImage game);\nuint32_t snap_texpack_gen(void);'),
            ('    ViewKey k = {img->image, img->format, vt, aspect, l0, nl, y0, ny, swz};',
             '    VkImage vimg = img->image;   // TEXPACK-01: a texture with an HD image is viewed on it, all of its levels\n'
             '    VkFormat vfmt = img->format;\n'
             '    uint32_t hd_levels = 0;\n'
             '    VkImage hd = storage || vt != VK_IMAGE_VIEW_TYPE_2D || aspect != VK_IMAGE_ASPECT_COLOR_BIT\n'
             '                     ? VK_NULL_HANDLE : snap_texpack_image(img->image, &vfmt, &hd_levels);\n'
             '    if (hd) vimg = hd, l0 = 0, nl = hd_levels, y0 = 0, ny = 1;\n'
             '    else vfmt = img->format;\n'
             '    ViewKey k = {vimg, vfmt, vt, aspect, l0, nl, y0, ny, swz};'),
            ('    VkImageViewCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = img->image, .viewType = vt,\n'
             '                                .format = img->format,',
             '    VkImageViewCreateInfo ci = {.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO, .image = vimg, .viewType = vt,\n'
             '                                .format = vfmt,'),
            ('    if (img->block_views) ci.pNext = &use;', '    if (img->block_views && !hd) ci.pNext = &use;'),
            ('    *n = (ViewNode){nvn_hm_get(&views_by_image, &img->image), k, view};\n    nvn_hm_put(&views_by_image, &img->image, n);',
             '    *n = (ViewNode){nvn_hm_get(&views_by_image, &vimg), k, view};\n    nvn_hm_put(&views_by_image, &vimg, n);'),
            ('    vk_exec_bc_gone(image);\n    snap_hd_photo_gone(image);',
             '    vk_exec_bc_gone(image);\n    snap_hd_photo_gone(image);\n    snap_texpack_gone(image);'),
            ('sg = vk_sampler_gen() + snap_hd_photo_gen();', 'sg = vk_sampler_gen() + snap_hd_photo_gen() + snap_texpack_gen();'),
        ],
    }
