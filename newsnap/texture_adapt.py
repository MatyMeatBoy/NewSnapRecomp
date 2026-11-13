"""Invalidate retired descriptors and add opt-in observational upload diagnostics.

The native fixture proves stale slot resurrection independently of the observed
DLSS crash. Whether that lifetime defect caused that particular crash is unproven.
"""
from pathlib import Path


UPLOAD_DIAGNOSTICS = r'''
// Snap upload diagnostics: no upload is skipped, thawed, or otherwise changed.
// tex_lock serializes this ring. Host NOACCESS can be a legitimate mem_hold.
typedef struct { char text[640]; } SnapUploadRecord;
static SnapUploadRecord snap_upload_ring[200];
static unsigned snap_upload_count, snap_upload_dumps;
static int snap_upload_trace_on(void) {
    const char *value = getenv("NEWSNAP_UPLOAD_TRACE");
    return value && !strcmp(value, "1");
}
static void snap_upload_record(const char *text, int suspect) {
    unsigned sequence = snap_upload_count++;
    unsigned long long frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    snprintf(snap_upload_ring[sequence % 200].text, 640, "frame=%llu %.600s", frame, text);
    if (sequence < 200) rt_log("upload_trace[%u]: %s", sequence, snap_upload_ring[sequence % 200].text);
    if (suspect) {
        rt_log("upload_trace suspect[%u]: %s", sequence, snap_upload_ring[sequence % 200].text);
        if (snap_upload_dumps++ < 3) {
            unsigned begin = snap_upload_count > 200 ? snap_upload_count - 200 : 0;
            for (unsigned i = begin; i < snap_upload_count; i++)
                rt_log("upload_trace history[%u]: %s", i, snap_upload_ring[i % 200].text);
        }
    }
}
static void snap_upload_gone(uint64_t lo, uint64_t size) {
    if (!snap_upload_trace_on()) return;
    char text[640];
    snprintf(text, sizeof text, "range_gone addr=%#llx size=%#llx",
             (unsigned long long)lo, (unsigned long long)size);
    snap_upload_record(text, 0);
}
static void snap_upload_trace(const tex_t *t, uint64_t addr, unsigned level, unsigned layer, size_t pitch) {
    if (!snap_upload_trace_on()) return;
    nvn_texlayout layout;
    nvn_tex_layout(&t->d, &layout);
    uint32_t row = 0, rows = 0, slices = 0, bpb = 0;
    uint64_t base = 0;
    unsigned th = 0, td = 0;
    int geom = nvn_deswizzle_geom(&t->d, level, layer, &row, &rows, &slices, &base, &th, &td, &bpb);
    uint64_t a = (uint64_t)(uintptr_t)t->mem, end = a + t->L.size, bad = 0;
    RtMemoryInfo guest = {0};
    int host = 0, logical_bad = end < a, host_bad = 0, held_possible = 0;
    uint64_t host_end = a;
    // Logical guest permissions distinguish freed/unmapped data from a mirror's
    // legitimate host NOACCESS hold. Queries are observations, not lifetime pins.
    for (uint64_t p = a; p < end;) {
        RtMemoryInfo q = {0};
        uint64_t next;
        if (mem_query(p, &q) || !(q.perm & 1) || q.base > p || q.size > UINT64_MAX - q.base
                || q.base + q.size <= p) {
            guest = q; bad = p; logical_bad = 1; break;
        }
        next = q.base + q.size;
        if (next > end) next = end;
        p = next;
    }
    for (uint64_t p = a; p < end;) {
        uint64_t next = p;
        int state = plat_mem_state(p, end, &next);
        if (state == PLAT_PROT_NONE) held_possible = 1;
        if (state < 0 || next <= p) {
            host = state; host_end = next; host_bad = 1;
            if (!bad) bad = p;
            break;
        }
        if (p == a) host = state, host_end = next;
        p = next;
    }
    int suspect = logical_bad || host_bad || layout.size != t->L.size || (!geom && base >= t->L.size);
    char text[640];
    snprintf(text, sizeof text,
        "deswizzle addr=%#llx mem=%#llx size=%#llx calculated=%#llx fmt=%#x target=%u "
        "whd=%ux%ux%u levels=%u level=%u layer=%u layer_size=%#llx pitch=%llu "
        "geom=%d base=%#llx row=%u rows=%u slices=%u th=%u td=%u "
        "bad=%#llx logical_bad=%d guest=%#llx+%#llx state=%#x perm=%#x "
        "host=%d host_end=%#llx held_possible=%d",
        (unsigned long long)addr, (unsigned long long)a, (unsigned long long)t->L.size,
        (unsigned long long)layout.size, t->d.format, t->d.target,
        t->d.width, t->d.height, t->d.depth, t->d.levels, level, layer,
        (unsigned long long)layout.layer_size, (unsigned long long)pitch, geom,
        (unsigned long long)base, row, rows, slices, th, td, (unsigned long long)bad, logical_bad,
        (unsigned long long)guest.base, (unsigned long long)guest.size, guest.state, guest.perm,
        host, (unsigned long long)host_end, held_possible);
    snap_upload_record(text, suspect);
}
'''


SLOT_LIFETIME_FIX = r'''
    // Snap: pool retirement happens after replay drain. A copied descriptor may
    // no longer recreate an image from this retired storage through slot_resolve.
    // Test overlap by subtraction: adjacent/empty ranges do not intersect and
    // address arithmetic never wraps a high range into low memory.
    int invalidated_slots = 0;
    for (int id = 0; size && id < ntslots; id++) {
        TexSlot *s = &tslots[id];
        uint64_t address = (uint64_t)(uintptr_t)s->t.mem, bytes = s->t.L.size;
        if (!s->used || !bytes) continue;
        int overlaps = address <= lo ? lo - address < bytes : address - lo < size;
        if (!overlaps) continue;
        s->used = 0;
        s->ce = NULL;
        s->cgen = s->cepoch = 0;
        s->t.mem = NULL;
        if (sinfo) __atomic_store_n(&sinfo[id], 0, __ATOMIC_RELEASE);
        invalidated_slots = 1;
    }
    if (invalidated_slots) slots_gen++;
'''


def adapt_texture_source(text):
    """Patch pinned seams; fail rather than silently missing either change."""
    if '// Snap: pool retirement happens after replay drain.' not in text:
        seam = '    pre_range_gone(lo, size, 0);\n    Tex **list ='
        if text.count(seam) != 1:
            raise ValueError('Pinned texture lifetime seam is missing or ambiguous')
        text = text.replace(seam, '    pre_range_gone(lo, size, 0);\n' + SLOT_LIFETIME_FIX + '\n    Tex **list =', 1)
    if '// Snap upload diagnostics:' in text:
        return text
    seams = {
        'static void upload(Tex *e) {': UPLOAD_DIAGNOSTICS + '\nstatic void upload(Tex *e) {',
        '            if (nvn_deswizzle(d, lv + skip, ly, t->mem, tmp ? tmp : dst, rb)) {':
            '            snap_upload_trace(t, e->pub.addr, lv + skip, ly, rb);\n'
            '            if (nvn_deswizzle(d, lv + skip, ly, t->mem, tmp ? tmp : dst, rb)) {',
        'void vk_texture_range_gone(uint64_t lo, uint64_t size, VmaAllocation alloc) {\n    lock();':
            'void vk_texture_range_gone(uint64_t lo, uint64_t size, VmaAllocation alloc) {\n    lock();\n'
            '    snap_upload_gone(lo, size);',
    }
    for old, new in seams.items():
        if text.count(old) != 1:
            raise ValueError('Pinned texture diagnostic seam is missing or ambiguous')
        text = text.replace(old, new, 1)
    return text


def patch_texture_diagnostics(runtime):
    path = Path(runtime) / 'vk_texture.c'
    original = path.read_text(encoding='utf-8')
    transformed = adapt_texture_source(original)
    if transformed != original:
        path.write_text(transformed, encoding='utf-8')
