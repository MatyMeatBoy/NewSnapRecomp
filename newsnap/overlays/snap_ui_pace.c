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

// RETICLE-HZ-01: the handler call in progress on this thread, by its stack pointer (the handler's frame is fixed
// after its prologue): draw_only_sp while it goes from its entry to its drawing section without stepping,
// placing_sp while that call runs the game's own loop over the positions asked for.
static _Thread_local uint64_t draw_only_sp, placing_sp;

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
    draw_only_sp = step ? 0 : c->sp;   // RETICLE-HZ-01: a call that only draws may still place its clips
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

// RETICLE-HZ-01. Game code places interface clips by name (object vtable +0xc0, main+0x799570: the camera's
// reticle and pointer `cursor_mc`, the brackets over a subject, markers): each call only queues {name, x, y} in the
// object (+0x810..+0x820). The handler applies the queue inside its logic (main+0x78d644..0x78d850: find the clip,
// main+0x9cd540 sets x, main+0x9cd660 sets y, then the queue is emptied). The game code that asks runs on every game
// frame with that frame's camera, but above 60 fps the handler's logic runs on interface steps only, so the clips
// moved 60 times a second over a scene drawn faster: the brackets trailed the subject and caught up in steps.
// On the frames that only draw, the handler now runs that one loop of its own before its drawing section: at the
// start of the drawing section (main+0x794b4c) x16 = 0 sends a draw-only call to the loop (main+0x78d644), and at
// the loop's end (main+0x78d850) x16 = 0 brings it back. A call that steps takes neither branch. The positions are
// the game's own, applied by the game's own code one to three frames earlier than before; on a step the queue holds
// only that frame's requests and ends in the same state as before (the last request for a clip wins either way), so
// what the interface logic and its scripts read on their steps does not change. At 60 fps and below no call is
// draw-only and nothing here runs. AC_SNAP_UI_POSITIONS_PATCH=0 removes both sites.
void snap_ui_pace_draw(Cpu *c) {
    if (placing_sp && placing_sp == c->sp) {   // back from the loop: draw
        placing_sp = 0;
        c->x[16] = 1;
        return;
    }
    if (!draw_only_sp || draw_only_sp != c->sp) {   // a call that stepped (or pacing off): draw as written
        c->x[16] = 1;
        return;
    }
    draw_only_sp = 0;
    placing_sp = c->sp;
    c->x[16] = 0;
}

void snap_ui_pace_placed(Cpu *c) {
    c->x[16] = !(placing_sp && placing_sp == c->sp);
}

// NEWSNAP_UI_POS_TRACE=1: every position asked for (main+0x799570: x0 object, x1 name, s0 x, s1 y) and every one
// applied (main+0x78d808: x19 the queue entry), with the presented frame, the game frame and whether it steps.
// NEWSNAP_UI_POS_TRACE=<text> keeps the names containing <text>.
static const char *pos_trace(void) {
    static const char *filter;
    static int on = -1;
    if (on < 0) {
        const char *e = getenv("NEWSNAP_UI_POS_TRACE");
        on = e && *e && strcmp(e, "0");
        filter = on && strcmp(e, "1") ? e : "";
    }
    return on ? filter : NULL;
}

// A libc++ string of the guest (short: length * 2 in byte 0, text from +1; long: bit 0 set, length +8, text at +0x10).
static int guest_string(uint64_t at, char *out, size_t size) {
    uint8_t s[24];
    out[0] = 0;
    if (!at || !plat_mem_read(at, s, sizeof s)) return 0;
    uint64_t length, text = at + 1;
    if (s[0] & 1) memcpy(&length, s + 8, 8), memcpy(&text, s + 16, 8);
    else length = s[0] >> 1;
    if (length >= size) length = size - 1;
    if (!plat_mem_read(text, out, (size_t)length)) return 0;
    out[length] = 0;
    return 1;
}

static void pos_log(const char *what, uint64_t object, const char *name, float x, float y, uint64_t from) {
    static unsigned lines;
    const char *filter = pos_trace();
    if (!filter || !strstr(name, filter) || __atomic_fetch_add(&lines, 1, __ATOMIC_RELAXED) >= 2000000) return;
    rt_log("snap_ui_pos: %s frame %llu game frame %llu step %d object %llx %s %.3f %.3f from %llx", what,
           (unsigned long long)__atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED), (unsigned long long)pad_tick,
           pace.step, (unsigned long long)object, name, (double)x, (double)y, (unsigned long long)from);
}

void snap_ui_pos_ask(Cpu *c) {
    if (!pos_trace()) return;
    char name[96];
    float x, y;
    uint32_t bx = (uint32_t)c->v[0], by = (uint32_t)c->v[1];
    memcpy(&x, &bx, 4), memcpy(&y, &by, 4);
    if (guest_string(c->x[1], name, sizeof name)) pos_log("ask", c->x[0], name, x, y, c->x[30] - 0x7000000000ull);
}

void snap_ui_pos_apply(Cpu *c) {
    if (!pos_trace()) return;
    char name[96];
    float xy[2];
    if (guest_string(c->x[19], name, sizeof name) && plat_mem_read(c->x[19] + 0x18, xy, sizeof xy))
        pos_log(placing_sp ? "place" : "apply", 0, name, xy[0], xy[1], 0);
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

// Arms the four breakpoints once on `first`, `first` + 4, + 8 and + 12 (every thread alive now) and logs the hits
// every 10 s of calls. `what` names the watched thing in the log.
static void watch_fields(uint64_t first, uint64_t now, const char *what) {
    static int armed;
    static uint64_t last_ns;
    if (!armed) {
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
                ctx.Dr0 = first, ctx.Dr1 = first + 4, ctx.Dr2 = first + 8, ctx.Dr3 = first + 12;
                ctx.Dr7 = 0x55 | 0xffff0000ull;   // DR0..DR3 enabled, read+write, 4 bytes each
                armed_threads += SetThreadContext(t, &ctx) != 0;
            }
            if (te.th32ThreadID != self) ResumeThread(t), CloseHandle(t);
        }
        CloseHandle(snap);
        rt_log("snap_ui_pace: %s watch on %llx (four 4-byte fields): %d threads, exe base %llx, this thread %lu", what,
               (unsigned long long)first, armed_threads, (unsigned long long)watch_base, (unsigned long)self);
        last_ns = now;
    }
    if (now - last_ns < 10000000000ull) return;
    last_ns = now;
    for (LONG i = 0; i < watch_count; i++)
        rt_log("snap_ui_pace: %s watch %s rva %llx thread %u: %u on steps, %u on other frames", what,
               (const char *[]){"+0", "+4", "+8", "+c"}[watch_hits[i].field],
               (unsigned long long)watch_hits[i].rip, watch_hits[i].thread, watch_hits[i].step, watch_hits[i].other);
}

static void watch_pad(uint64_t pad, uint64_t now) {
    static int on = -1;
    static uint64_t at = 0x54;   // first of four 4-byte fields
    if (on < 0) {
        const char *w = getenv("NEWSNAP_PAD_WATCH"), *offset = getenv("NEWSNAP_PAD_WATCH_AT");
        on = w && !strcmp(w, "1");
        if (offset) at = strtoull(offset, NULL, 16);
    }
    if (on) watch_fields(pad + at, now, "pad");
}

// NEWSNAP_UI_POS_WATCH=<clip name> (with the pad watch off): the same breakpoints on a clip the game places, at
// NEWSNAP_UI_POS_WATCH_AT (hex, default 88: the first four floats of its matrix on screen), to name the code that
// reads and writes a clip's transform and whether it runs on interface steps only.
static void watch_clip(uint64_t clip, const char *name) {
    static int on = -1;
    static const char *wanted;
    static uint64_t at = 0x88;
    if (on < 0) {
        const char *offset = getenv("NEWSNAP_UI_POS_WATCH_AT");
        wanted = getenv("NEWSNAP_UI_POS_WATCH");
        on = wanted && *wanted;
        if (offset) at = strtoull(offset, NULL, 16);
    }
    if (on && clip && !strcmp(name, wanted)) watch_fields(clip + at, kern_now_ns(), name);
}
#else
static void watch_pad(uint64_t pad, uint64_t now) { (void)pad; (void)now; }
static void watch_clip(uint64_t clip, const char *name) { (void)clip; (void)name; }
#endif

// The clip a queued position is about to be applied to (main+0x78d68c: x0, found by name; main+0x78d7ac: x22, found
// by path), x19 the queue entry: only for the clip watch.
static void motion_placed(uint64_t clip);
static void pos_clip(uint64_t clip, uint64_t entry) {
    static int watch = -1;
    char name[96];
    motion_placed(clip);
    if (watch < 0) watch = getenv("NEWSNAP_UI_POS_WATCH") != NULL;
    if (watch && guest_string(entry, name, sizeof name)) watch_clip(clip, name);
}
void snap_ui_pos_clip_named(Cpu *c) { pos_clip(c->x[0], c->x[19]); }
void snap_ui_pos_clip_path(Cpu *c) { pos_clip(c->x[22], c->x[19]); }

// The other transforms game code asks for by clip name, queued and applied the same way (NEWSNAP_UI_POS_TRACE):
// width and height (vtable entry main+0x799950, queue +0x858), scale (main+0x799b20, +0x870) and rotation
// (main+0x7995f0, +0x8a0). x0 object, x1 name, s0 and s1 the values.
static void transform_ask(Cpu *c, const char *what) {
    if (!pos_trace()) return;
    char name[96];
    float a, b;
    uint32_t ba = (uint32_t)c->v[0], bb = (uint32_t)c->v[1];
    memcpy(&a, &ba, 4), memcpy(&b, &bb, 4);
    if (guest_string(c->x[1], name, sizeof name)) pos_log(what, c->x[0], name, a, b, c->x[30] - 0x7000000000ull);
}
void snap_ui_size_ask(Cpu *c) { transform_ask(c, "size"); }
void snap_ui_scale_ask(Cpu *c) { transform_ask(c, "scale"); }
void snap_ui_rotation_ask(Cpu *c) { transform_ask(c, "rotation"); }

// MENU-FPS-01 (snap_ui_motion.h). The interface player draws a movie in two passes over its clips: each clip's
// matrix on screen (+0x88, six floats) is brought up to date from its own matrix (+0x70) and its parent's (+0x40)
// (vtable +0x30), then each clip that draws something hands that matrix to the renderer (renderer vtable +0x20)
// before its shapes or text (vtable +0x38: shapes main+0x9b5be0, text main+0x9b60c0 and main+0x9b78a0; the two
// container classes hand nothing). At those three calls x1, the matrix handed over, is replaced by the matrix on
// the way from the last interface step's to this one's when the clip is in motion. Above 60 fps only, while the
// interface is paced; AC_SNAP_UI_MOTION_PATCH=0 removes the three sites. NEWSNAP_UI_MOTION_TRACE=1 logs the counts.
#include "snap_ui_motion.h"
static SnapUiMotion motion;
static int motion_lock;
static uint64_t step_count;                              // interface steps so far
static int motion_on;                                    // set by the pad update of a paced game frame
static float motion_phase;                               // real time since this step was due, in steps
static struct { uint64_t clip, tick; } placed[32];       // clips the game placed by name lately

static void motion_placed(uint64_t clip) {
    uint64_t tick = pad_tick;
    int oldest = 0;
    for (int i = 0; i < 32; i++) {
        if (placed[i].clip == clip) { placed[i].tick = tick; return; }
        if (placed[i].tick < placed[oldest].tick) oldest = i;
    }
    placed[oldest].clip = clip, placed[oldest].tick = tick;
}

void snap_ui_motion_hand(Cpu *c) {
    uint64_t key = c->x[1];
    if (!motion_on || !key) return;
    static uint64_t handed, blended, window_ns;
    uint64_t tick = pad_tick;
    int live = 0;
    uint64_t object = key - 0x88;
    for (int depth = 0; depth < 16 && object && !live; depth++) {   // the clip and the clips it is inside
        for (int i = 0; i < 32; i++)
            if (placed[i].clip == object && tick - placed[i].tick < SNAP_UI_MOTION_LIVE_FRAMES) { live = 1; break; }
        object = *(const uint64_t *)(uintptr_t)(object + 0x40);
    }
    while (__atomic_test_and_set(&motion_lock, __ATOMIC_ACQUIRE)) {}
    const float *out = snap_ui_motion_matrix(&motion, key, (const float *)(uintptr_t)key, tick, step_count, pace.step,
                                             motion_phase, live);
    handed++, blended += (uint64_t)(uintptr_t)out != key;
    __atomic_clear(&motion_lock, __ATOMIC_RELEASE);
    c->x[1] = (uint64_t)(uintptr_t)out;
    if (!pace_trace()) return;
    uint64_t now = kern_now_ns();
    if (!window_ns) window_ns = now;
    if (now - window_ns < 5000000000ull) return;
    rt_log("snap_ui_motion: %llu matrices handed over, %llu of them between two steps", (unsigned long long)handed,
           (unsigned long long)blended);
    window_ns = now, handed = blended = 0;
}

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
        int paced = cap && cap + SNAP_UI_PACE_SLACK_NS < SNAP_UI_PACE_STEP_NS;
        if (pace.step) step_count++;
        motion_phase = (float)((double)pace.acc_ns / (double)SNAP_UI_PACE_STEP_NS);
        motion_on = paced;
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

// FPS-02. The interface pointer (main+0x643a70: pause menu, photo selection, Photodex) moves by its speed times the
// game's frame time over 1/60 s ([timer+0x1c], main+0x643cc8), and by its speed per call when that time is 0. Paused
// screens hand it 0, others a fixed 1/60 s per call; either way it moved a fixed step per frame, 2.4 times as fast at
// 144 fps. Above 60 fps the time is always the real time of the game frame, so the pointer keeps its speed on every
// screen; at 60 fps and below nothing changes. x16 is not used; s1 is the loaded time.
void snap_ui_pace_pointer(Cpu *c) {
    uint64_t cap = frame_step_cap_ns();
    if (!cap || cap + SNAP_UI_PACE_SLACK_NS >= SNAP_UI_PACE_STEP_NS) return;
    float t;
    uint32_t bits = (uint32_t)c->v[1];
    memcpy(&t, &bits, 4);
    // Every screen with the pointer: some hand it 0 (paused), others a fixed 1/60 s a call (the Photodex), and both
    // move it once per frame. Above 60 fps it always gets the real time of the game frame.
    if (pace_trace()) {
        static unsigned lines;
        if (lines++ < 64) rt_log("snap_ui_pace: pointer frame time from the game %.5f s", (double)t);
    }
    // A steady step: the average real frame time (exponential, about 16 frames). The game thread's own frame times
    // jitter (it runs ahead and then waits), and stepping by each of them moved the pointer in uneven steps; the
    // average keeps every step even and the distance per second right, also when the game runs under its limit. A
    // real hitch (over two average frames) steps by its own time so the pointer does not fall behind.
    static double average;
    uint64_t real = __atomic_load_n(&pad_dt_ns, __ATOMIC_RELAXED);
    if (!real || real > SNAP_UI_PACE_MAX_DT_NS) real = cap;
    average = average > 0 ? average + ((double)real - average) / 16.0 : (double)cap;
    uint64_t dt = (double)real > 2.0 * average ? real : (uint64_t)average;
    if (dt < 1000000ull) dt = 1000000ull;
    t = (float)((double)dt / 1e9);
    memcpy(&bits, &t, 4);
    c->v[1] = bits;
}
