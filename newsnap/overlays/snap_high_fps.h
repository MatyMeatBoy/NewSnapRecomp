// Discrete opt-in rates. Keep the game's slower present intervals intact.
#pragma once
#include <stdint.h>
#include <string.h>

static inline unsigned snap_fps_parse(const char *value) {
    if (value && !strcmp(value, "30")) return 30;
    if (value && !strcmp(value, "90")) return 90;
    if (value && !strcmp(value, "120")) return 120;
    if (value && !strcmp(value, "144")) return 144;
    return 60;
}

// "display" (PACE-AMD-01): the smallest whole fraction of the monitor refresh at or above ~60, so FIFO shows every
// frame for the same number of refreshes (144 Hz -> 72, 100 -> 100, 120 -> 60, 165 -> 82.5, 59.94 -> 59.94).
// A plain 60 cap on 144 Hz alternates 2 and 3 refreshes (13.9/20.8 ms). Same idea as Zelda64Recomp's
// "Framerate: Display". Unknown or implausible refresh: 60.
static inline double snap_fps_display(double refresh_hz) {
    if (!(refresh_hz >= 50.0 && refresh_hz <= 1000.0)) return 60.0;
    unsigned n = (unsigned)(refresh_hz / 59.0);
    if (n < 1) n = 1;
    return refresh_hz / n;
}

// "vrr" (VRR-02): just under the monitor refresh, so a variable-refresh display (FreeSync, G-SYNC) stays inside its
// range instead of reaching the top, where the driver falls back to V-Sync or tears: refresh - refresh^2 / 3600
// (144 Hz -> 138.24, 120 -> 116, 165 -> 157.44, 240 -> 224, 60 -> 59). Unknown or implausible refresh: 60.
static inline double snap_fps_vrr(double refresh_hz) {
    if (!(refresh_hz >= 50.0 && refresh_hz <= 1000.0)) return 60.0;
    return refresh_hz - refresh_hz * refresh_hz / 3600.0;
}

static inline double snap_fps_target(const char *value, double refresh_hz) {
    if (value && !strcmp(value, "display")) return snap_fps_display(refresh_hz);
    if (value && !strcmp(value, "vrr")) return snap_fps_vrr(refresh_hz);
    return snap_fps_parse(value);
}

static inline uint64_t snap_fps_period(uint64_t ticks, uint64_t cap) {
    uint64_t native = ticks * UINT64_C(1000000000) / 60;
    // Only lift the ordinary 60 Hz path. An authored interval of 2 or more
    // remains a native 30/20/... Hz scene, even with a high frame cap.
    if (ticks == 1 && cap < UINT64_C(1000000000) / 60) return cap;
    return native > cap ? native : cap;
}
