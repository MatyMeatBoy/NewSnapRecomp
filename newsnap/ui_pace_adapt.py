"""UI-HZ-01: declare the interface pacing helpers for the guest patch table.

The patch set (patches/snap-2.0.1-ui-pace.txt) and the overlay (overlays/snap_ui_pace.c) make the
interface handler's logic, its Flash-style timelines and its per-frame event run 60 times a second
of real time above 60 fps, while the interface is still drawn on every frame. Nothing here changes
behaviour by itself.

AC_SHOTS_DEFER=1 (development): a series of consecutive presents (AC_SHOTS=lo-hi:1, or by game seconds with
AC_SHOTS=w<lo>-<hi>:0.001) is kept in memory and written when the range ends. Writing each picture as it is presented takes longer than a 60 Hz frame, so the
game dropped under 60 fps during the series and every frame stepped the interface: such a series showed
nothing of what happens between two steps.
"""

DEFERRED_SHOTS = '''// AC_SHOTS_DEFER=1: the pictures of a series of presents stay in memory (at most SNAP_DEFER_MAX, full size) and are
// written after the range or when the run ends, so taking them does not slow the frames they show.
#define SNAP_DEFER_MAX 240
static struct { uint8_t *px; uint32_t w, h; int bgra; unsigned long long n; } snap_deferred[SNAP_DEFER_MAX];
static unsigned snap_deferred_count;
static const char *snap_deferred_dir;

static int snap_shots_defer(uint8_t *px, uint32_t w, uint32_t h, int bgra, unsigned long long n, const char *dir) {
    static int on = -1;
    if (on < 0) on = cfg_get("AC_SHOTS_DEFER") != NULL;
    if (!on || snap_deferred_count >= SNAP_DEFER_MAX) return 0;
    snap_deferred[snap_deferred_count].px = px, snap_deferred[snap_deferred_count].w = w;
    snap_deferred[snap_deferred_count].h = h, snap_deferred[snap_deferred_count].bgra = bgra;
    snap_deferred[snap_deferred_count++].n = n;
    snap_deferred_dir = dir;
    return 1;
}

static void snap_shots_flush(void) {
    for (unsigned i = 0; i < snap_deferred_count; i++) {
        uint8_t *px = snap_deferred[i].px;
        uint64_t count = (uint64_t)snap_deferred[i].w * snap_deferred[i].h;
        for (uint64_t k = 0; k < count; k++) {
            if (snap_deferred[i].bgra) { uint8_t b = px[4 * k]; px[4 * k] = px[4 * k + 2], px[4 * k + 2] = b; }
            px[4 * k + 3] = 255;
        }
        char path[PLAT_PATH_MAX];
        snprintf(path, sizeof path, "%s/f%05llu.png", snap_deferred_dir, snap_deferred[i].n);
        rt_write_png(path, px, snap_deferred[i].w, snap_deferred[i].h);
        free(px);
    }
    snap_deferred_count = 0;
}

'''


def edits():
    return {'runtime/cpu.h': [
        ('typedef void (*GuestFn)(Cpu *);',
         'void snap_ui_pace_enter(Cpu *c);\nvoid snap_ui_pace_event(Cpu *c);\nvoid snap_ui_pace_pad(Cpu *c);\nvoid snap_ui_pace_pointer(Cpu *c);\n'
         'void snap_ui_pace_draw(Cpu *c);\nvoid snap_ui_pace_placed(Cpu *c);\nvoid snap_ui_pos_ask(Cpu *c);\nvoid snap_ui_pos_apply(Cpu *c);\n'
         'void snap_ui_pos_clip_named(Cpu *c);\nvoid snap_ui_pos_clip_path(Cpu *c);\nvoid snap_ui_size_ask(Cpu *c);\n'
         'void snap_ui_scale_ask(Cpu *c);\nvoid snap_ui_rotation_ask(Cpu *c);\nvoid snap_ui_motion_hand(Cpu *c);\n'
         'void snap_ui_pace_advance(Cpu *c);\nvoid snap_ui_pace_ptrbits(Cpu *c);\n'
         'typedef void (*GuestFn)(Cpu *);'),
    ], 'runtime/cfg.c': [
        # MENU-FPS-01: ui_motion = 0|1 in the settings file (AC_UI_MOTION), the switch of the snap_ui_motion patch set
        ('"HD_SHADOWS", "TEX_PACK", "TEX_PACK_SAVE",', '"HD_SHADOWS", "TEX_PACK", "TEX_PACK_SAVE", "UI_MOTION",'),
        ('{"TEX_PACK_SAVE", "display"},', '{"TEX_PACK_SAVE", "display"}, {"UI_MOTION", "display"},'),
        ('{"TEX_PACK_SAVE", "0", "0|1", RESTART},', '{"TEX_PACK_SAVE", "0", "0|1", RESTART}, {"UI_MOTION", "1", "0|1", RESTART},'),
    ], 'runtime/boot.c': [
        ('// AC_SHOTS=lo-hi:step [AC_SHOTS_DIR=dir]: every step-th present',
         DEFERRED_SHOTS + '// AC_SHOTS=lo-hi:step [AC_SHOTS_DIR=dir]: every step-th present'),
        ('    } else if (n < lo || n > hi || (n - lo) % step) {\n        return;\n    }',
         '    } else if (n < lo || n > hi || (n - lo) % step) {\n        if (n > hi) snap_shots_flush();\n        return;\n    }'),
        ('    if (gfx_replay_async()) gfx_backend()->finish();   // the presented frame may still be queued for the replay\n'
         '    gfx_backend()->read_texels(t, &view, &r, px, 4ull * w, 4ull * w * h);\n'
         '    for (uint32_t y = 0; y < oh; y++)',
         '    if (gfx_replay_async()) gfx_backend()->finish();   // the presented frame may still be queued for the replay\n'
         '    gfx_backend()->read_texels(t, &view, &r, px, 4ull * w, 4ull * w * h);\n'
         '    if (snap_shots_defer(px, w, h, bgra, n, dir)) { free(out); return; }\n'
         '    for (uint32_t y = 0; y < oh; y++)'),
        ('        if (w < 0 || (unsigned long long)w < next || next > hi) return;',
         '        if (w >= 0 && next > hi) snap_shots_flush();\n'
         '        if (w < 0 || (unsigned long long)w < next || next > hi) return;'),
        ('    if (cfg->shot) save_shot(t, cfg->shot);\n    GfxStats g = gfx_stats();',
         '    snap_shots_flush();\n    if (cfg->shot) save_shot(t, cfg->shot);\n    GfxStats g = gfx_stats();'),
    ]}
