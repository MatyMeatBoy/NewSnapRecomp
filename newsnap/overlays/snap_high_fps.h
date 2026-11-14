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

static inline uint64_t snap_fps_period(uint64_t ticks, uint64_t cap) {
    uint64_t native = ticks * UINT64_C(1000000000) / 60;
    // Only lift the ordinary 60 Hz path. An authored interval of 2 or more
    // remains a native 30/20/... Hz scene, even with a high frame cap.
    if (ticks == 1 && cap < UINT64_C(1000000000) / 60) return cap;
    return native > cap ? native : cap;
}
