"""Discrete presentation caps and read-only timing observations for Snap."""


def edits():
    return {'runtime/cpu.h': [
        ('typedef void (*GuestFn)(Cpu *);',
         'void snap_timer_observe(Cpu *c);\nvoid snap_rail_observe(Cpu *c);\nvoid snap_pad_observe(Cpu *c);\nvoid snap_event_observe(Cpu *c);\n'
         'void snap_ui_state_observe(Cpu *c);\nvoid snap_ui_event_observe(Cpu *c);\n'
         'typedef void (*GuestFn)(Cpu *);'),
    ], 'runtime/cfg.c': [
        ('{"FPS", "60", "30|60", LIVE}', '{"FPS", "60", "30|60|90|120|144|display|vrr", LIVE}'),
    ], 'runtime/frame_rate.c': [
        ('#include "cfg.h"', '#include "cfg.h"\n#include "snap_high_fps.h"'),
        ('static int fps60_on = -1, fps_hz;',
         '''static int fps60_on = -1, fps_hz;
static double snap_cap_hz, snap_refresh_seen = -1;
double gfx_window_refresh_hz(void);'''),
        ('if (fps_read && v == fps_seen) return;',
         '''double snap_refresh = gfx_window_refresh_hz();
    if (fps_read && v == fps_seen && snap_refresh == snap_refresh_seen) return;
    snap_refresh_seen = snap_refresh;'''),
        ('int hz = cfg_int("AC_FPS");',
         '''double snap_exact = snap_fps_target(cfg_value("AC_FPS"), snap_refresh);
    int hz = (int)(snap_exact + 0.5);
    if (snap_exact != snap_cap_hz && fps_hz == hz) rt_log("frame rate: %.3f fps (display)", snap_exact);
    snap_cap_hz = snap_exact;'''),
        ('return (uint64_t)(1e9 / fps_hz + 0.5);', 'return (uint64_t)(1e9 / (snap_cap_hz > 0 ? snap_cap_hz : fps_hz) + 0.5);'),
        ('fps_hz == (hz >= 60 ? 60 : 30)', 'fps_hz == hz'),
        ('fps_hz = hz >= 60 ? 60 : 30;', 'fps_hz = hz;'),
        ('if (interval > 0) step_now = interval / 60.0;',
         '''if (interval > 0) step_now = fps_hz > 60
        ? (dt > 0 ? (dt > STEP_MAX_S ? STEP_MAX_S : dt) : 1.0 / fps_hz)
        : interval / 60.0; // Script ticks use clamped presentation deltas above 60, not present count.'''),
        ('%.3f s game stepped, speed %.3f;', '%.3f s presentation clock, ratio %.3f;'),
    ], 'runtime/nvn_api_obj.c': [
        ('#define VSYNC_HZ 60ull', '#include "snap_high_fps.h"\n#define VSYNC_HZ 60ull'),
        ('''uint64_t native_period = ticks * 1000000000ull / VSYNC_HZ;
    uint64_t cap_period = frame_step_cap_ns();
    return native_period > cap_period ? native_period : cap_period;''',
         'return snap_fps_period(ticks, frame_step_cap_ns());'),
    ], 'runtime/ui/menu.cpp': [
        ('''    static const char *const vals[] = {"30", "60"};
    static const UiTextId ids[] = {UI_MENU_FPS_30, UI_MENU_FPS_60};
    enum { N = sizeof vals / sizeof *vals };
    const char *names[N];
    for (int i = 0; i < N; i++) names[i] = menu_text(ids[i]);
    const char *set = cfg_get("AC_FPS");
    int cur = set && !strcmp(set, "30") ? 0 : 1;''',
         '''    static const char *const vals[] = {"30", "60", "90", "120", "144", "vrr"};
    enum { N = sizeof vals / sizeof *vals };
    // "vrr" (VRR-02): just under the display's refresh, inside a FreeSync / G-SYNC range (138 at 144 Hz)
    const char *names[N] = {menu_text(UI_MENU_FPS_30), menu_text(UI_MENU_FPS_60), "90 FPS", "120 FPS", "144 FPS",
                            "VRR"};
    const char *set = cfg_get("AC_FPS");
    int cur = 1;
    for (int i = 0; set && i < N; i++) if (!strcmp(set, vals[i])) cur = i;'''),
    ]}
