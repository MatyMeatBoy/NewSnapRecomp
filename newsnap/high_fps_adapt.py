"""Discrete presentation caps and read-only timing observations for Snap."""


def edits():
    return {'runtime/cpu.h': [
        ('typedef void (*GuestFn)(Cpu *);',
         'void snap_timer_observe(Cpu *c);\nvoid snap_rail_observe(Cpu *c);\n'
         'void snap_ui_state_observe(Cpu *c);\nvoid snap_ui_event_observe(Cpu *c);\n'
         'typedef void (*GuestFn)(Cpu *);'),
    ], 'runtime/cfg.c': [
        ('{"FPS", "60", "30|60", LIVE}', '{"FPS", "60", "30|60|90|120|144", LIVE}'),
    ], 'runtime/frame_rate.c': [
        ('#include "cfg.h"', '#include "cfg.h"\n#include "snap_high_fps.h"'),
        ('int hz = cfg_int("AC_FPS");', 'int hz = (int)snap_fps_parse(cfg_value("AC_FPS"));'),
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
         '''    static const char *const vals[] = {"30", "60", "90", "120", "144"};
    enum { N = sizeof vals / sizeof *vals };
    const char *names[N] = {menu_text(UI_MENU_FPS_30), menu_text(UI_MENU_FPS_60), "90 FPS", "120 FPS", "144 FPS"};
    const char *set = cfg_get("AC_FPS");
    int cur = 1;
    for (int i = 0; set && i < N; i++) if (!strcmp(set, vals[i])) cur = i;'''),
    ]}
