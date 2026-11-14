"""FOTO-01: 2D BC render targets through stand-ins on AMD's RDNA 1/2 driver.

The donor already draws 3D BC images through an uncompressed stand-in because AMD's
RDNA 2 driver writes past the memory of a BLOCK_TEXEL_VIEW_COMPATIBLE image (donor
issue #5). Snap encodes its in-level photo thumbnail to BC1 by drawing through such a
view of a 2D image; on the owner's RX 6900 XT (26.10.1) that gave the banded thumbnail,
striped BC UI textures and "write invalid" device faults. AC_BLOCK_VIEWS (default off
on that driver branch, vk_caps.amd_sc; on elsewhere) sends 2D BC targets the same way.
"""

TEXTURE_BEFORE = '''               bv3d);
    }
    if (!ds && samples == 1 && f.vk == f.ideal && nvn_fmt_bpb(d->format, &bw, &bh) && bw == 4 && bh == 4 &&
        (type != VK_IMAGE_TYPE_3D || bv3d)) {'''

TEXTURE_AFTER = '''               bv3d);
    }
    // AC_BLOCK_VIEWS (default 0 on AMD's RDNA 1/2 driver branch, vk_caps.amd_sc; 1 elsewhere): a 2D BC image gets
    // block views. NewSnap FOTO-01: on an RX 6900 XT (26.10.1) Snap's BC1 encoder of the photo thumbnail draws through
    // such a view; the thumbnail came out with one stretch in four and black elsewhere, BC UI textures beside it took
    // stripes and the device faulted ("write invalid"), the overrun of issue #5. Without block views those draws go
    // through a stand-in, as for 3D BC images (vk_exec.c bc_target).
    static int bv2d = -1;
    if (bv2d < 0) {
        bv2d = rt_knob("BLOCK_VIEWS", vk_caps.amd_sc ? "0" : "1");
        rt_log("vk: 2D BC textures %s (AC_BLOCK_VIEWS=%d%s)",
               bv2d ? "get block views (renderable)" : "are drawn through stand-ins", bv2d,
               vk_caps.amd_sc ? ", AMD RDNA 1/2 driver" : "");
    }
    if (!ds && samples == 1 && f.vk == f.ideal && nvn_fmt_bpb(d->format, &bw, &bh) && bw == 4 && bh == 4 &&
        (type == VK_IMAGE_TYPE_3D ? bv3d : bv2d)) {'''

EXEC_EDITS = [
    ('''typedef struct { VkImage bc, img; VmaAllocation alloc; VkFormat fmt; uint32_t level, w, h, d; } BcStandIn;
#define BC_STANDINS 64   // one per level drawn: 6 volumes of up to 7 levels at the logo''',
     '''// A 2D BC texture without block views (vk_texture.c create_tex, AC_BLOCK_VIEWS: off on AMD's RDNA 1/2 driver, NewSnap
// FOTO-01) goes the same way, one stand-in layer per array layer. Its stand-in is refreshed from the level at each
// pass begin (bc_refresh, flat), so content the texture took since (uploads, copies, other passes) is not overwritten
// by stale stand-in blocks at the pass end.
typedef struct { VkImage bc, img; VmaAllocation alloc; VkFormat fmt; uint32_t level, w, h, d; uint8_t flat; } BcStandIn;
#define BC_STANDINS 256   // one per level drawn: 6 volumes of up to 7 levels at the logo, plus 2D BC targets'''),
    ('''    uint32_t lw = level_extent(img->width, level), lh = level_extent(img->height, level);
    BcStandIn s = {img->image, VK_NULL_HANDLE, NULL, fmt, level, (lw + 3) / 4, (lh + 3) / 4,
                   level_extent(img->depth, level)};''',
     '''    uint32_t lw = level_extent(img->width, level), lh = level_extent(img->height, level);
    int flat = img->type != VK_IMAGE_TYPE_3D;
    BcStandIn s = {img->image, VK_NULL_HANDLE, NULL, fmt, level, (lw + 3) / 4, (lh + 3) / 4,
                   flat ? (img->layers ? img->layers : 1) : level_extent(img->depth, level), (uint8_t)flat};'''),
    ('''    VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, level, 0, 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, s.d},
                      .extent = {lw, lh, s.d}};   // texels of the compressed source''',
     '''    VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, level, 0, flat ? s.d : 1},
                      .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, s.d},
                      .extent = {lw, lh, flat ? 1 : s.d}};   // texels of the compressed source'''),
    ('''    rt_log("vk: 3D BC render target %ux%ux%u level %u drawn through a %ux%u x %u stand-in (format %d)", img->width,
           img->height, img->depth, level, s.w, s.h, s.d, (int)fmt);''',
     '''    static int logged2d;
    if (!flat)
        rt_log("vk: 3D BC render target %ux%ux%u level %u drawn through a %ux%u x %u stand-in (format %d)", img->width,
               img->height, img->depth, level, s.w, s.h, s.d, (int)fmt);
    else if (logged2d < 16)
        logged2d++, rt_log("vk: 2D BC render target %ux%u (vk format %d) level %u drawn through a %ux%u x %u stand-in "
                           "(format %d)", img->width, img->height, (int)img->format, level, s.w, s.h, s.d, (int)fmt);'''),
    ('''        VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, t->base_layer, t->layers},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, bcs[i].level, 0, 1},
                          .dstOffset = {0, 0, (int32_t)t->base_layer},
                          .extent = {bcs[i].w, bcs[i].h, t->layers}};   // texels of the uncompressed source''',
     '''        int flat = bcs[i].flat;
        VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, t->base_layer, t->layers},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, bcs[i].level, flat ? t->base_layer : 0,
                                             flat ? t->layers : 1},
                          .dstOffset = {0, 0, flat ? 0 : (int32_t)t->base_layer},
                          .extent = {bcs[i].w, bcs[i].h, flat ? 1 : t->layers}};   // texels of the uncompressed source'''),
    ('''// A draw into a 3D BC image without block views through an uncompressed view of its blocks: the target is the
// image's stand-in (bc_standin). 1 when o is filled (target or left out), 0 for any other target.
static int bc_target(const tex_t *t, const view_t *v, int has_v, const VkTexImage *img, VkExecTarget *o) {
    int bw, bh;
    if (img->type != VK_IMAGE_TYPE_3D || img->block_views || !nvn_fmt_bpb(t->d.format, &bw, &bh) || bw != 4 || bh != 4)
        return 0;''',
     '''// At a pass begin (outside rendering): a 2D stand-in takes its texture's current blocks of the layers the pass draws,
// so a pass that writes part of them keeps the rest (bc_copy_back copies all of them back at the pass end).
static void bc_refresh(VkExec *ex, const VkExecTarget *t) {
    plat_mutex_lock(&bcs_lock);
    for (int i = 0; i < nbcs; i++) {
        if (bcs[i].img != t->image) continue;
        if (!bcs[i].flat) break;
        memory_barrier(ex->cb, VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, VK_ACCESS_2_MEMORY_WRITE_BIT, VK_PIPELINE_STAGE_2_COPY_BIT,
                       VK_ACCESS_2_TRANSFER_READ_BIT | VK_ACCESS_2_TRANSFER_WRITE_BIT);
        VkImageCopy rg = {.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, bcs[i].level, t->base_layer, t->layers},
                          .dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, t->base_layer, t->layers},
                          .extent = {level_extent(t->img->width, bcs[i].level), level_extent(t->img->height, bcs[i].level),
                                     1}};   // texels of the compressed source
        vkCmdCopyImage(ex->cb, bcs[i].bc, VK_IMAGE_LAYOUT_GENERAL, t->image, VK_IMAGE_LAYOUT_GENERAL, 1, &rg);
        memory_barrier(ex->cb, VK_PIPELINE_STAGE_2_COPY_BIT, VK_ACCESS_2_TRANSFER_WRITE_BIT,
                       VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT, VK_ACCESS_2_MEMORY_READ_BIT | VK_ACCESS_2_MEMORY_WRITE_BIT);
        ex->recorded++;
        break;
    }
    plat_mutex_unlock(&bcs_lock);
}

// A draw into a BC image without block views (3D, or 2D with AC_BLOCK_VIEWS=0) through an uncompressed view of its
// blocks: the target is the image's stand-in (bc_standin). 1 when o is filled (target or left out), 0 for any other.
static int bc_target(const tex_t *t, const view_t *v, int has_v, const VkTexImage *img, VkExecTarget *o) {
    int bw, bh;
    if ((img->type != VK_IMAGE_TYPE_3D && img->type != VK_IMAGE_TYPE_2D) || img->block_views || img->samples > 1 ||
        !nvn_fmt_bpb(t->d.format, &bw, &bh) || bw != 4 || bh != 4)
        return 0;'''),
    ('    if (img && !depth_slot && bc_target(t, v, has_v, img, o)) return;   // a 3D BC image: its stand-in',
     '    if (img && !depth_slot && bc_target(t, v, has_v, img, o)) return;   // a BC image without block views: its stand-in'),
    ('    barrier_to(ex, want, wasp, nwant);   // passes, clears, copies and dispatches see each other\'s results',
     '''    barrier_to(ex, want, wasp, nwant);   // passes, clears, copies and dispatches see each other's results
    for (uint32_t i = 0; i < ex->pass_ncolor && i < 8; i++)   // 2D BC stand-ins take their textures' current blocks
        if (ex->color[i].image && ex->color[i].img && ex->color[i].img->image != ex->color[i].image)
            bc_refresh(ex, &ex->color[i]);'''),
    ('    if (ex->in_pass || t->is3d || t->blocks || t->width != ex->pass_w || t->height != ex->pass_h) return 0;',
     '''    // nor a stand-in of a BC image (bc_target): only a pass end copies a stand-in back to its texture
    if (ex->in_pass || t->is3d || t->blocks || (t->img && t->img->image != t->image) || t->width != ex->pass_w ||
        t->height != ex->pass_h)
        return 0;'''),
]


def edits():
    return {
        'runtime/vk_texture.c': [(TEXTURE_BEFORE, TEXTURE_AFTER)],
        'runtime/vk_exec.c': list(EXEC_EDITS),
        'runtime/cfg.c': [('"BIND_ZL", "BIND_ZR", "BLOCK_VIEWS_3D",', '"BIND_ZL", "BIND_ZR", "BLOCK_VIEWS", "BLOCK_VIEWS_3D",')],
    }
