"""PIPE-MO-01: prewarm the per-object motion pipelines instead of dropping them at every boot.

The per-object motion pass (FSR 4 / DLAA object motion, vk_exec_draw.c) redraws
moving objects with a fragment shader of the runtime's own (mo_fs), which has no
guest input id. vk_pipeline.c records each built pipeline in pipeline-keys.bin
naming its shaders by input id, so these records carry has_fs 1 with an all-zero
id; the boot prewarm then drops them ("shader neither cached nor stored": 92 of
275 records on the owner's RX 6900 XT, 99 of 286 after more play) and every one is
built again during play. With graphics pipeline libraries off on AMD's RDNA 1/2
driver, a draw whose pipeline is still building is skipped or waits: missing
object motion for the upscaler, or a hitch.

The record's spare pad word now names the shader's output location (tag "MO");
the prewarm recreates the same shader with mo_fs(location), the very object the
draw uses, so the pipeline key matches. Old records without the tag are still
dropped as before. Independent of the GPU vendor.
"""

DRAW_BEFORE = '''        if (!MO.fs[loc]) MO.failed = 1, rt_log("vk_exec: the per-object motion fragment shader is malformed: off");
    }
    return MO.fs[loc];
}'''

DRAW_AFTER = DRAW_BEFORE + '''

// NewSnap PIPE-MO-01: vk_pipeline.c names this shader in pipeline-keys.bin by its output location (it has no guest
// input id) and recreates it at the boot prewarm. -1: not a per-object motion shader.
int snap_mo_fs_location(const GfxShader *s) {
    for (int i = 0; s && i < 32; i++)
        if (MO.fs[i] == s) return i;
    return -1;
}

const GfxShader *snap_mo_fs_get(int loc) { return mo_fs(loc); }'''

REC_BEFORE = '''static void rec_fill(KeyRec *r, const VkPipeState *s) {
    memset(r, 0, sizeof *r);
    memcpy(r->vs, gfx_shader_input_id(s->vs), 32);
    if (s->fs) memcpy(r->fs, gfx_shader_input_id(s->fs), 32), r->has_fs = 1;'''

REC_AFTER = '''// NewSnap PIPE-MO-01 (vk_exec_draw.c): the per-object motion fragment shader has no guest input id; KeyRec.pad names
// its output location under this tag so the boot prewarm can recreate it instead of dropping the record.
#define SNAP_MO_KEY_TAG 0x4d4f0000u
int snap_mo_fs_location(const GfxShader *s);
const GfxShader *snap_mo_fs_get(int loc);

static void rec_fill(KeyRec *r, const VkPipeState *s) {
    memset(r, 0, sizeof *r);
    memcpy(r->vs, gfx_shader_input_id(s->vs), 32);
    if (s->fs) {
        memcpy(r->fs, gfx_shader_input_id(s->fs), 32), r->has_fs = 1;
        int loc = snap_mo_fs_location(s->fs);
        if (loc >= 0) r->pad = SNAP_MO_KEY_TAG | (uint32_t)loc;
    }'''

COUNT_BEFORE = '    uint32_t queued = 0, dropped = 0, known = 0;'
COUNT_AFTER = '    uint32_t queued = 0, dropped = 0, known = 0, snap_mo = 0;'

LOOP_BEFORE = '''        const GfxShader *vs = v ? sh[v - ids] : NULL, *fs = f ? sh[f - ids] : NULL;
        if (!vs || (r[i].has_fs && !fs)) {'''

LOOP_AFTER = '''        const GfxShader *vs = v ? sh[v - ids] : NULL, *fs = f ? sh[f - ids] : NULL;
        if (vs && r[i].has_fs && !fs && (r[i].pad & 0xffff0000u) == SNAP_MO_KEY_TAG &&
            (fs = snap_mo_fs_get((int)(r[i].pad & 0xffu))))
            snap_mo++;   // NewSnap PIPE-MO-01: the per-object motion shader, recreated from its location
        if (!vs || (r[i].has_fs && !fs)) {'''

LOG_BEFORE = '''    K.loading = 0;
    plat_mutex_unlock(&P.lock);
    free(ids), free(sh);'''

LOG_AFTER = '''    K.loading = 0;
    plat_mutex_unlock(&P.lock);
    free(ids), free(sh);
    if (snap_mo) rt_log("vk_pipeline: prewarm: %u per-object motion pipelines recreated from their shader location", snap_mo);'''


def edits():
    return {
        'runtime/vk_exec_draw.c': [(DRAW_BEFORE, DRAW_AFTER)],
        'runtime/vk_pipeline.c': [(REC_BEFORE, REC_AFTER), (COUNT_BEFORE, COUNT_AFTER), (LOOP_BEFORE, LOOP_AFTER),
                                  (LOG_BEFORE, LOG_AFTER)],
    }
