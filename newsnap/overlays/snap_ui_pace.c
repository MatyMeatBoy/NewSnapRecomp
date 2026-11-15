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
static uint64_t pad_tick, pad_tick_ns, pad_dt_ns;   // pad_dt_ns: real time between the last two game frames
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

// INPUT-HZ-01. The game's pad update (main+0x925b60) runs once a game frame. The game reads it through its input
// queries: held buttons (main+0x43c160) from one byte per button (+0x54..+0x73), and newly pressed buttons
// (main+0x43c2d0, 26 callers) by comparing those bytes with the copy the update keeps of the previous frame's
// (+0x74..+0x93); the update also keeps masks (+0x44 held, +0x48 pressed, +0x4c released, +0x50 previous).
// Above 60 fps the interface handlers step only on some frames, while the code that queries the pad runs on every
// frame: a press seen on a frame where the interface did not step completed the dialogue line, and the interface
// then took the same press, on its next step, as the order to go on to the next line.
// The game expects a pad sampled once per update of its logic, 60 times a second. So above 60 fps the pad changes
// only on the game frames whose interface steps: on the others it shows the buttons of the last step and nothing
// newly pressed or released; on a step it shows the real buttons, compared with the last step's, and a press that
// came and went in between counts as pressed for that step. Every reader then sees each press once, on a frame
// where the interface also sees it, as at 60 fps; a press arrives at most one step (16.7 ms) later. Sticks are not
// touched. The interface decision is taken here as well, once per game frame (pace_step).
#define PAD_BYTES 32
static struct { uint64_t pad; uint32_t mask, between_mask; uint8_t bytes[PAD_BYTES], between[PAD_BYTES]; } pad_held[4];

// NEWSNAP_PAD_WATCH=1 (Windows, diagnostics): hardware data breakpoints on the pad's held buttons (+0x44, DR0) and
// pressed edges (+0x48, DR1) on the game thread; every 10 s the host code addresses that touched them are logged with
// their counts, split by interface step, so the readers can be named from the linker map (f_<guest address>).
#ifdef _WIN32
#include <windows.h>
#include <tlhelp32.h>
static struct { uint64_t rip; uint32_t field, step, other, thread; } watch_hits[192];
static volatile LONG watch_count;
static uint64_t watch_base;

static LONG CALLBACK watch_handler(EXCEPTION_POINTERS *e) {
    if (e->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) return EXCEPTION_CONTINUE_SEARCH;
    DWORD64 dr6 = e->ContextRecord->Dr6;
    if (!(dr6 & 15)) return EXCEPTION_CONTINUE_SEARCH;
    uint64_t rip = (uint64_t)e->ContextRecord->Rip - watch_base;
    uint32_t field = (dr6 & 1) ? 0 : (dr6 & 2) ? 1 : (dr6 & 4) ? 2 : 3;
    LONG n = watch_count;
    int i = 0;
    uint32_t thread = GetCurrentThreadId();
    while (i < n && !(watch_hits[i].rip == rip && watch_hits[i].field == field && watch_hits[i].thread == thread)) i++;
    if (i == n && n < 192) watch_hits[i].rip = rip, watch_hits[i].field = field, watch_hits[i].thread = thread, watch_count = n + 1;
    if (i < 192) { if (pace.step) watch_hits[i].step++; else watch_hits[i].other++; }
    e->ContextRecord->Dr6 = 0;
    return EXCEPTION_CONTINUE_EXECUTION;
}

static void watch_pad(uint64_t pad, uint64_t now) {
    static int armed;
    static uint64_t last_ns;
    if (!armed) {
        const char *w = getenv("NEWSNAP_PAD_WATCH");
        if (!w || strcmp(w, "1")) { armed = -1; return; }
        armed = 1;
        watch_base = (uint64_t)(uintptr_t)GetModuleHandleW(NULL);
        AddVectoredExceptionHandler(1, watch_handler);
        DWORD self = GetCurrentThreadId(), pid = GetCurrentProcessId();
        HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        THREADENTRY32 te = {.dwSize = sizeof te};
        int armed_threads = 0;
        for (BOOL more = Thread32First(snap, &te); more; more = Thread32Next(snap, &te)) {
            if (te.th32OwnerProcessID != pid) continue;
            HANDLE t = te.th32ThreadID == self ? GetCurrentThread()
                     : OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
            if (!t) continue;
            if (te.th32ThreadID != self) SuspendThread(t);
            CONTEXT ctx = {0};
            ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
            if (GetThreadContext(t, &ctx)) {
                const char *at = getenv("NEWSNAP_PAD_WATCH_AT");   // first of four 4-byte fields, default +0x54
                uint64_t first = pad + (at ? strtoull(at, NULL, 16) : 0x54);
                ctx.Dr0 = first, ctx.Dr1 = first + 4, ctx.Dr2 = first + 8, ctx.Dr3 = first + 12;
                ctx.Dr7 = 0x55 | 0xffff0000ull;   // DR0..DR3 enabled, read+write, 4 bytes each
                armed_threads += SetThreadContext(t, &ctx) != 0;
            }
            if (te.th32ThreadID != self) ResumeThread(t), CloseHandle(t);
        }
        CloseHandle(snap);
        rt_log("snap_ui_pace: pad watch on %llx (+0x44, +0x48): %d threads, exe base %llx, this thread %lu",
               (unsigned long long)pad, armed_threads, (unsigned long long)watch_base, (unsigned long)self);
        last_ns = now;
    }
    if (armed < 0 || now - last_ns < 10000000000ull) return;
    last_ns = now;
    for (LONG i = 0; i < watch_count; i++)
        rt_log("snap_ui_pace: pad watch %s rva %llx thread %u: %u on steps, %u on other frames", (const char *[]){"+0", "+4", "+8", "+c"}[watch_hits[i].field],
               (unsigned long long)watch_hits[i].rip, watch_hits[i].thread, watch_hits[i].step, watch_hits[i].other);
}
#else
static void watch_pad(uint64_t pad, uint64_t now) { (void)pad; (void)now; }
#endif

void snap_ui_pace_pad(Cpu *c) {
    uint64_t cap = frame_step_cap_ns(), pad = c->x[19], now = kern_now_ns();
    if (!pad || !plat_mem_readable(pad + 0x44, 0x50)) return;
    int slot = 0;
    while (slot < 4 && pad_held[slot].pad && pad_held[slot].pad != pad) slot++;
    if (slot == 4) return;   // more pads than the game has: leave them as they are
    if (!pad_held[slot].pad) {   // first update: the last step is what the pad shows now
        pad_held[slot].pad = pad;
        memcpy(&pad_held[slot].mask, (void *)(uintptr_t)(pad + 0x44), 4);
        memcpy(pad_held[slot].bytes, (void *)(uintptr_t)(pad + 0x54), PAD_BYTES);
    }
    if (slot == 0) watch_pad(pad, now);
    if (slot == 0) {   // the first pad marks the game frame: the decision for the handlers until its next update
        uint64_t before = __atomic_load_n(&pad_tick_ns, __ATOMIC_RELAXED);
        __atomic_store_n(&pad_dt_ns, before && now > before ? now - before : 0, __ATOMIC_RELAXED);
        snap_ui_pace_decide(&pace, pad_tick++, now, cap);
        __atomic_store_n(&pad_tick_ns, now, __ATOMIC_RELEASE);
    }
    uint32_t *mask = (uint32_t *)(uintptr_t)(pad + 0x44);   // [0] held, [1] pressed, [2] released, [3] previous
    uint8_t *bytes = (uint8_t *)(uintptr_t)(pad + 0x54), *previous = bytes + PAD_BYTES;
    if (!cap || cap + SNAP_UI_PACE_SLACK_NS >= SNAP_UI_PACE_STEP_NS) {   // 60 fps or below: every frame steps
        pad_held[slot].mask = mask[0];
        memcpy(pad_held[slot].bytes, bytes, PAD_BYTES);
        return;
    }
    if (pace.step) {
        uint32_t last = pad_held[slot].mask, held = mask[0];
        uint32_t taps = pad_held[slot].between_mask & ~last & ~held;   // pressed and released between two steps
        held |= taps;
        mask[0] = held, mask[1] = held & ~last, mask[2] = last & ~held, mask[3] = last;
        for (int i = 0; i < PAD_BYTES; i++) {
            if (pad_held[slot].between[i] && !pad_held[slot].bytes[i] && !bytes[i]) bytes[i] = pad_held[slot].between[i];
            previous[i] = pad_held[slot].bytes[i];
        }
        pad_held[slot].mask = held, pad_held[slot].between_mask = 0;
        memcpy(pad_held[slot].bytes, bytes, PAD_BYTES);
        memset(pad_held[slot].between, 0, PAD_BYTES);
    } else {
        pad_held[slot].between_mask |= mask[0];
        for (int i = 0; i < PAD_BYTES; i++) if (bytes[i]) pad_held[slot].between[i] = bytes[i];
        mask[0] = mask[3] = pad_held[slot].mask, mask[1] = mask[2] = 0;
        memcpy(bytes, pad_held[slot].bytes, PAD_BYTES);
        memcpy(previous, pad_held[slot].bytes, PAD_BYTES);
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
    rt_log("snap_event: frame %llu game frame %llu step %d object %llx event %u from%s",
           (unsigned long long)__atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED), (unsigned long long)pad_tick, pace.step,
           (unsigned long long)c->x[0], (unsigned)c->x[1], chain);
}

// FPS-02. The interface pointer (main+0x643a70: pause menu, photo selection) moves by its speed times the game's
// frame time over 1/60 s ([timer+0x1c], main+0x643cc8), and by its speed per call when that time is 0, which it is
// while the game is paused: in the pause menu the pointer moved a fixed step per frame, 2.4 times as fast at
// 144 fps. Above 60 fps a frame time of 0 or less is replaced by the real time of the game frame, so the pointer
// keeps its speed at any rate; at 60 fps and below nothing changes. x16 is not used; s1 is the loaded time.
void snap_ui_pace_pointer(Cpu *c) {
    uint64_t cap = frame_step_cap_ns();
    if (!cap || cap + SNAP_UI_PACE_SLACK_NS >= SNAP_UI_PACE_STEP_NS) return;
    float t;
    uint32_t bits = (uint32_t)c->v[1];
    memcpy(&t, &bits, 4);
    if (t > 0.0f) return;
    uint64_t dt = __atomic_load_n(&pad_dt_ns, __ATOMIC_RELAXED);
    if (!dt || dt > SNAP_UI_PACE_MAX_DT_NS) dt = cap;
    if (dt < 1000000ull) dt = 1000000ull;
    t = (float)((double)dt / 1e9);
    memcpy(&bits, &t, 4);
    c->v[1] = bits;
}
