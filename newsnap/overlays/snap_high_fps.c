// Snap 2.0.1 timer exit observation. No guest writes and no Cpu changes.
#include <stdint.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "host.h"
#include "platform/platform.h"

// Verified libc++ string layout at the two UI observation boundaries. Read
// only bounded printable names; unknown/long/invalid descriptors are skipped.
static int ui_string(uint64_t address, char out[96]) {
    uint8_t object[24];
    if (!address || !plat_mem_read(address, object, sizeof object)) return 0;
    uint64_t size, data;
    if (object[0] & 1) {
        memcpy(&size, object + 8, 8); memcpy(&data, object + 16, 8);
        if (size >= 96 || !data || !plat_mem_read(data, out, (size_t)size)) return 0;
    } else {
        size = object[0] >> 1;
        if (size > 22) return 0;
        memcpy(out, object + 1, (size_t)size);
    }
    for (uint64_t i = 0; i < size; i++) if ((unsigned char)out[i] < 32 || (unsigned char)out[i] > 126) return 0;
    out[size] = 0;
    return 1;
}

static void ui_log(uint64_t player, uint64_t state_address, int event) {
    static _Thread_local unsigned lines;
    char state[96], scene[96];
    if (lines >= 2048 || player > UINT64_MAX - 0x10 || !ui_string(state_address, state) ||
        !ui_string(player + 0x10, scene)) return;
    lines++;
    rt_log("snap_ui: wall_ns %llu player %llx event %d scene %s state %s",
           (unsigned long long)kern_now_ns(), (unsigned long long)player, event, scene, state);
}

void snap_ui_state_observe(Cpu *c) {
    const char *trace = getenv("NEWSNAP_UI_TRACE");
    if (!trace || strcmp(trace, "1") || c->x[1] > UINT64_MAX - 0x18) return;
    ui_log(c->x[0], c->x[1] + 0x18, 0);
}

void snap_ui_event_observe(Cpu *c) {
    const char *trace = getenv("NEWSNAP_UI_TRACE");
    if (!trace || strcmp(trace, "1")) return;
    int event;
    uint64_t player;
    if (!plat_mem_read(c->x[1], &event, sizeof event) ||
        (event != 2 && event != 3 && event != 5 && event != 6 && event != 7) ||
        !plat_mem_read(c->x[2], &player, sizeof player)) return;
    ui_log(player, c->x[3], event);
}

void snap_rail_observe(Cpu *c) {
    const char *trace = getenv("NEWSNAP_RAIL_TRACE");
    if (!trace || strcmp(trace, "1")) return;
    uint8_t bytes[0x74], curve_bytes[0x40];
    if (!plat_mem_read(c->x[19], bytes, sizeof bytes)) return;
    uint64_t curve;
    float progress, length;
    memcpy(&curve, bytes + 0x30, 8);
    memcpy(&progress, bytes + 0x70, 4);
    if (!curve || !plat_mem_read(curve, curve_bytes, sizeof curve_bytes)) return;
    memcpy(&length, curve_bytes + 0x3c, 4);
    if (!isfinite(progress) || !isfinite(length) || length <= 0 ||
        length > 1e6f || progress < 0 || progress > length + 1) return;
    static _Thread_local uint64_t object, epoch;
    static _Thread_local float last;
    static _Thread_local unsigned lines;
    if (lines >= 1024) return;
    uint64_t now = kern_now_ns();
    if (object != c->x[19] || progress < last - 0.5f) {
        object = c->x[19]; epoch = now; last = -1;
    }
    if (progress - last < 1 && progress < length) return;
    last = progress; lines++;
    rt_log("snap_rail: object %llx wall_ns %llu elapsed_ns %llu progress %.9g length %.9g",
           (unsigned long long)object, (unsigned long long)now,
           (unsigned long long)(now - epoch), progress, length);
}

void snap_timer_observe(Cpu *c) {
    const char *trace = getenv("NEWSNAP_TIMER_TRACE");
    if (!trace || strcmp(trace, "1")) return;
    uint8_t bytes[0x58];
    if (!plat_mem_read(c->x[19], bytes, sizeof bytes)) return;
    // The timer's owning guest thread is the sole writer. TLS avoids collecting
    // unrelated callers into the same sample if another instance is discovered.
    static _Thread_local uint64_t start, calls;
    static _Thread_local double sums[3];
    static _Thread_local uint64_t ms_sums[3];
    static _Thread_local unsigned fixed[3], paused[3];
    uint64_t now = kern_now_ns();
    if (!start) start = now;
    unsigned modes[3];
    float deltas[3];
    for (unsigned i = 0; i < 3; i++) {
        memcpy(&modes[i], bytes + 0x18 + i * 0x18, 4);
        memcpy(&deltas[i], bytes + 0x1c + i * 0x18, 4);
        uint64_t ms;
        memcpy(&ms, bytes + 0x10 + i * 0x18, 8);
        ms_sums[i] += ms;
        sums[i] += deltas[i];
        fixed[i] += modes[i] == 1;
        paused[i] += bytes[0x24 + i * 0x18] != 0;
    }
    if (++calls % 120) return;
    rt_log("snap_timer: calls %llu wall_ns %llu mode %u/%u/%u dt %.9g/%.9g/%.9g sum %.9g/%.9g/%.9g fixed %u/%u/%u paused %u/%u/%u ms_sum %llu/%llu/%llu object %llx",
           (unsigned long long)calls, (unsigned long long)(now - start),
           modes[0], modes[1], modes[2], deltas[0], deltas[1], deltas[2],
           sums[0], sums[1], sums[2], fixed[0], fixed[1], fixed[2], paused[0], paused[1], paused[2],
           (unsigned long long)ms_sums[0], (unsigned long long)ms_sums[1], (unsigned long long)ms_sums[2],
           (unsigned long long)c->x[19]);
}
