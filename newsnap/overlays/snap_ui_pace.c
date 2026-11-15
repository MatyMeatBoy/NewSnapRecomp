// UI-HZ-01 (Snap 2.0.1 main ddb900ff04a912ed42430508389853cfaf1accce only).
//
// The interface is a Flash-style player driven by the game's interface objects. Once per game frame
// the interface system calls each object's handler (main+0x7835d0). The handler runs the object's
// logic and advances its movies one timeline frame (main+0x9d0de0, loops at 0x7838f8 and 0x790dfc);
// then, in its last section (main+0x794b4c), it draws the movies (main+0x9d1e80) and raises the
// game's per-frame event 22 (main+0x794b90). Nothing takes a time step: the interface's logic, its
// timelines and its per-frame event all count frames, so everything runs with the frame rate.
//
// Above 60 fps, on the frames that are not due, the handler goes straight to its drawing
// section and leaves without raising the per-frame event. Logic, timelines and that event then run
// together 60 times a second of real time, and the interface is drawn on every frame from the state
// the last update left. Objects the handler would not have drawn (not started, or its early-out
// flags) take the original path untouched.
// What did not work, and why this shape: (1) returning from the movie advance and (2) raising the
// movie's own step threshold: clips the game created were drawn before the player initialised them
// (every language of the logo at once, hidden menus); (3) skipping the whole handler: the interface
// is drawn inside it, so dialogue boxes blinked; (4) holding only each sprite's enterFrame event and
// timeline frame: the game's own frame counters ran ahead of the clips (a hint panel looped in and out).
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "host.h"
#include "gfx.h"
#include "platform/platform.h"
#include "snap_ui_pace.h"

extern GfxStats gfx_counters;   // nvn_api.h; frames: presented frames

static SnapUiPace pace = {0, 0, 0, 1};
static uint64_t ran, drawn_only, window_ns, window_frame;

static int pace_trace(void) {
    static int on = -1;
    if (on < 0) {
        const char *e = getenv("NEWSNAP_UI_PACE_TRACE");
        on = e && !strcmp(e, "1");
    }
    return on;
}

// The game frame: the game's pad update (snap_ui_pace_pad) runs once in each, so while it runs the interface
// decision is taken there, once per game frame, and every handler until the next update uses it. The presented-frame
// counter is advanced by the presentation thread and can change in the middle of a game frame; it only paces the
// interface when no pad update has run for a while (PAD_GAP_NS).
#define PAD_GAP_NS 100000000ull
static uint64_t pad_tick, pad_tick_ns;
static SnapUiPace pace_presented = {0, 0, 0, 1};

static int pace_step(uint64_t now) {
    uint64_t seen = __atomic_load_n(&pad_tick_ns, __ATOMIC_ACQUIRE);
    if (seen && now >= seen && now - seen < PAD_GAP_NS) return __atomic_load_n(&pace.step, __ATOMIC_RELAXED);
    uint64_t frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    return snap_ui_pace_decide(&pace_presented, frame, now, frame_step_cap_ns());
}

// At the handler's entry, after it saved its object (x0): x16 (dead here) = 1 to run the handler as
// written, 0 to branch to its drawing section. The shortcut is only taken for an object in the state
// the handler itself would carry on from: started (+0xc0), ready (+0xc6) and not held (+0xc4).
void snap_ui_pace_enter(Cpu *c) {
    uint64_t now = kern_now_ns();
    int step = pace_step(now);
    if (!step) {
        uint8_t flags[8];
        if (!c->x[0] || !plat_mem_read(c->x[0] + 0xc0, flags, sizeof flags) || !flags[0] || !flags[6] || flags[4])
            step = 1;
    }
    c->x[16] = (uint64_t)step;
    if (!pace_trace()) return;
    if (!pace.step && step) {   // a frame that does not step, an object that still runs: log each such object once
        static uint64_t seen[64];
        static int nseen;
        int known = 0;
        for (int i = 0; i < nseen; i++) known |= seen[i] == c->x[0];
        if (!known && nseen < 64) {
            uint8_t flags[8] = {0};
            plat_mem_read(c->x[0] + 0xc0, flags, sizeof flags);
            seen[nseen++] = c->x[0];
            rt_log("snap_ui_pace: object %llx runs on every frame (flags +c0 %02x +c4 %02x +c6 %02x)",
                   (unsigned long long)c->x[0], flags[0], flags[4], flags[6]);
        }
    }
    ran += step, drawn_only += !step;
    uint64_t frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    if (!window_ns) window_ns = now, window_frame = frame;
    if (now - window_ns < 5000000000ull) return;
    double seconds = (double)(now - window_ns) / 1e9;
    rt_log("snap_ui_pace: %.1f s: %.1f frames a second; handlers run %llu (%.1f a second), drawn only %llu; "
           "frame period %.3f ms", seconds, (double)(frame - window_frame) / seconds, (unsigned long long)ran,
           (double)ran / seconds, (unsigned long long)drawn_only, (double)frame_step_cap_ns() / 1e6);
    window_ns = now, window_frame = frame, ran = drawn_only = 0;
}

// Before the handler raises the per-frame event 22: x16 = 1 to raise it, 0 to leave.
void snap_ui_pace_event(Cpu *c) {
    c->x[16] = (uint64_t)pace_step(kern_now_ns());
}

// INPUT-HZ-01. The game's pad update (main+0x925b60) runs once a game frame. It keeps the buttons held (+0x44) and
// the previous update's (+0x50), and from them the edges (+0x48 pressed, +0x4c released) that last until the next
// update. Some readers act on the edges every frame, others on the held buttons at their own pace; above 60 fps the
// interface handlers step only on some frames, so the two kinds saw one press at different times and a press in the
// middle of a dialogue line completed it and also went on to the next line, as if A had been pressed twice. The
// game expects a pad sampled at 60 Hz, once per update of its logic. So above 60 fps the pad changes only on the
// game frames whose interface steps: on the others its buttons stay as on the last step and it has no edges; on a
// step the game's own comparison with that state gives the edges, and a press that came and went in between is
// kept as a press and a release. Every reader then sees each press once, at the same frame, as at 60 fps; a press
// arrives at most one step (16.7 ms) later. The sticks are not touched.
// The interface decision is taken here as well, once per game frame (pace_step), so the pad and the interface
// handlers agree on which frames step.
static struct { uint64_t pad; uint32_t between; } pad_held[4];

void snap_ui_pace_pad(Cpu *c) {
    uint64_t cap = frame_step_cap_ns(), pad = c->x[19], now = kern_now_ns();
    if (!pad || !plat_mem_readable(pad + 0x44, 16)) return;
    int slot = 0;
    while (slot < 4 && pad_held[slot].pad && pad_held[slot].pad != pad) slot++;
    if (slot == 4) return;   // more pads than the game has: leave them as they are
    pad_held[slot].pad = pad;
    if (slot == 0) {   // the first pad marks the game frame: the decision for the handlers until its next update
        snap_ui_pace_decide(&pace, pad_tick++, now, cap);
        __atomic_store_n(&pad_tick_ns, now, __ATOMIC_RELEASE);
    }
    if (!cap || cap + SNAP_UI_PACE_SLACK_NS >= SNAP_UI_PACE_STEP_NS) return;   // 60 fps or below: every frame steps
    uint32_t *state = (uint32_t *)(uintptr_t)(pad + 0x44);   // [0] held, [1] pressed, [2] released, [3] previous
    uint32_t held = state[0], previous = state[3];
    if (pace_trace() && (state[1] | state[2] | pad_held[slot].between))
        rt_log("snap_ui_pace: pad exit game frame %llu held %x pressed %x released %x previous %x between %x step %d",
               (unsigned long long)pad_tick, held, state[1], state[2], previous, pad_held[slot].between, pace.step);
    if (pace.step) {
        uint32_t taps = pad_held[slot].between & ~previous & ~held;   // pressed and released between two steps
        state[1] |= taps, state[2] |= taps;
        pad_held[slot].between = 0;
    } else {
        pad_held[slot].between |= held;
        state[0] = previous, state[1] = state[2] = 0;
    }
}

// The guest call chain from the frame records (x29, saved x30 at [x29+8]) as main offsets.
static void guest_chain(Cpu *c, char *chain, size_t size) {
    int n = 0;
    uint64_t fp = c->x[29];
    chain[0] = 0;
    for (int i = 0; i < 12 && fp; i++) {
        uint64_t rec[2];
        if (!plat_mem_read(fp, rec, sizeof rec)) break;
        uint64_t off = rec[1] - 0x7000000000ull;
        n += snprintf(chain + n, size - (size_t)n, " %llx", (unsigned long long)(off < 0x2891000ull ? off : rec[1]));
        if (n >= (int)size - 20 || rec[0] <= fp) break;
        fp = rec[0];
    }
}

// The game's pad object at its update (main+0x925b60, x1): +0x44 buttons, +0x48 pressed, +0x4c released, as the
// previous update left them. NEWSNAP_PAD_TRACE=1 logs each update that follows a press or a release, with the
// presented frame, so the cadence of the update and the life of a press can be read against the frame rate.
void snap_pad_observe(Cpu *c) {
    static int on = -1;
    if (on < 0) {
        const char *trace = getenv("NEWSNAP_PAD_TRACE");
        on = trace && !strcmp(trace, "1");
    }
    if (!on) return;
    static uint64_t calls, window_ns, window_calls, window_frame;
    static unsigned lines;
    uint32_t state[3];
    uint64_t now = kern_now_ns(), frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    calls++;
    if (!window_ns) window_ns = now, window_frame = frame;
    if (now - window_ns >= 5000000000ull) {
        rt_log("snap_pad: %llu updates in %llu frames", (unsigned long long)(calls - window_calls),
               (unsigned long long)(frame - window_frame));
        window_ns = now, window_calls = calls, window_frame = frame;
    }
    if (lines >= 4096 || !plat_mem_read(c->x[1] + 0x44, state, sizeof state) || !(state[1] | state[2])) return;
    lines++;
    rt_log("snap_pad: frame %llu call %llu pad %llx buttons %x pressed %x released %x (interface step %d)",
           (unsigned long long)frame, (unsigned long long)calls, (unsigned long long)c->x[1], state[0], state[1], state[2],
           pace.step);
}

// The interface's event raise (main+0x7a9a70: x0 object, w1 event), NEWSNAP_PAD_TRACE=1: every event but the
// per-frame one (22), with the presented frame.
void snap_event_observe(Cpu *c) {
    static int on = -1;
    static unsigned lines;
    if (on < 0) {
        const char *trace = getenv("NEWSNAP_PAD_TRACE");
        on = trace && !strcmp(trace, "1");
    }
    if (!on || (uint32_t)c->x[1] == 22 || lines >= 20000) return;
    lines++;
    char chain[200];
    guest_chain(c, chain, sizeof chain);
    rt_log("snap_event: frame %llu step %d object %llx event %u from%s",
           (unsigned long long)__atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED), pace.step,
           (unsigned long long)c->x[0], (unsigned)c->x[1], chain);
}

// The interface object's state request (main+0x79bd90: x0 object, x1 the requested state name), NEWSNAP_PAD_TRACE=1:
// the request, whether this frame is an interface step, and the guest call chain (frame records x29/x30) as main
// offsets, to name the game code asking for each change.
void snap_request_observe(Cpu *c) {
    static int on = -1;
    static unsigned lines;
    if (on < 0) {
        const char *trace = getenv("NEWSNAP_PAD_TRACE");
        on = trace && !strcmp(trace, "1");
    }
    if (!on || lines >= 20000) return;
    lines++;
    char name[40] = "?";
    uint8_t s[24];
    if (c->x[1] && plat_mem_read(c->x[1], s, sizeof s)) {
        uint64_t size = 0, data = 0;
        if (s[0] & 1) { memcpy(&size, s + 8, 8); memcpy(&data, s + 16, 8); }
        if (!(s[0] & 1) && (s[0] >> 1) < 23) { size = s[0] >> 1; memcpy(name, s + 1, size); name[size] = 0; }
        else if (size && size < sizeof name && data && plat_mem_read(data, name, size)) name[size] = 0;
        else if (plat_mem_read(c->x[1], name, sizeof name - 1)) name[sizeof name - 1] = 0;
        for (char *p = name; *p; p++) if (*p < 32 || *p > 126) { *p = 0; break; }
    }
    char chain[200];
    int n = 0;
    uint64_t fp = c->x[29];
    for (int i = 0; i < 10 && fp; i++) {
        uint64_t rec[2];
        if (!plat_mem_read(fp, rec, sizeof rec)) break;
        uint64_t off = rec[1] - 0x7000000000ull;
        n += snprintf(chain + n, sizeof chain - (size_t)n, " %llx", (unsigned long long)(off < 0x2891000ull ? off : rec[1]));
        if (n >= (int)sizeof chain - 20 || rec[0] <= fp) break;
        fp = rec[0];
    }
    chain[n] = 0;
    rt_log("snap_request: frame %llu step %d object %llx state %s from%s",
           (unsigned long long)__atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED), pace.step,
           (unsigned long long)c->x[0], name, chain);
}
