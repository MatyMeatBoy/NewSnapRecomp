// FG-02: when a generated frame fits the monitor (snap_fsr_fg.c snap_fg_rate_ok).
#pragma once
#include <stdint.h>

// want: the real rate is at most 0.55 of the panel's (or either is unknown). The state
// changes only after 2 s of disagreement, so it does not flicker around the limit.
static inline int snap_fg_rate_decide(double real_hz, double panel_hz, int current, uint64_t now_ns, uint64_t *since_ns) {
    int want = panel_hz <= 0 || real_hz <= 0 || real_hz <= 0.55 * panel_hz;
    if (want == current) { *since_ns = 0; return current; }
    if (!*since_ns) *since_ns = now_ns ? now_ns : 1;   // 0 means "no disagreement yet"
    if (now_ns < *since_ns + 2000000000ull) return current;
    *since_ns = 0;
    return want;
}
