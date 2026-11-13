// Optional host-input evidence. Call only under input.c's lock. No changes to guest input.
// NEWSNAP_INPUT_TRACE=1: at most 512 records per lane; changed samples or a 60-frame heartbeat.
#pragma once
#include <stdint.h>
#include <string.h>

static inline void snap_input_trace(unsigned lane, uint64_t frame,
                                    int32_t a, int32_t b, int32_t c, int32_t d, uint64_t buttons) {
    static struct {
        uint64_t frame, logged_frame, buttons;
        int32_t value[4];
        unsigned count;
    } state[2];
    if (lane >= 2) return;
    const char *enabled = cfg_get("NEWSNAP_INPUT_TRACE");
    if (!enabled || strcmp(enabled, "1")) return;
    if (state[lane].count >= 512 || (state[lane].count && frame == state[lane].frame)) return;
    state[lane].frame = frame;
    const int32_t value[4] = {a, b, c, d};
    int changed = state[lane].buttons != buttons || memcmp(value, state[lane].value, sizeof value);
    if (state[lane].count && !changed && frame - state[lane].logged_frame < 60) return;
    memcpy(state[lane].value, value, sizeof value);
    state[lane].buttons = buttons;
    state[lane].logged_frame = frame;
    state[lane].count++;
    rt_log("snap input: %s frame=%llu a=%d b=%d c=%d d=%d buttons=%#llx record=%u/512",
           lane ? "merged(Lx,Ly,Rx,Ry)" : "mouse(dx,dy,stickx,sticky)",
           (unsigned long long)frame, a, b, c, d, (unsigned long long)buttons, state[lane].count);
}
