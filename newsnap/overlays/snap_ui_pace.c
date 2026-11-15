// UI-HZ-01 (Snap 2.0.1 main ddb900ff04a912ed42430508389853cfaf1accce only).
//
// The game's interface is a Flash-style player: movie clips with timelines. Once per game frame
// the interface manager walks its list of movies and advances each by exactly one timeline frame
// (main+0x9d0de0, called from the loops at main+0x7838f8 and main+0x790dfc). The call takes no
// time step, so at 144 fps every menu, popup, score screen and loading animation runs 2.4 times
// faster while the 3D scene, which uses the measured timer, keeps its speed.
//
// Above 60 fps this holds the movies on the frames that are not due: before each walk
// (main+0x7838e4, main+0x790de8) the frame's one decision is looked up (made from real time, 60
// steps a second, once per presented frame: the manager walks its lists several times a frame), and on
// a held frame the movie pointer the loop just loaded is replaced by an empty stand-in that the
// player's own first check rejects (its owner has no root), so the original call returns at once.
// The loop, the list and every register besides x0 are untouched. At 60 fps and below nothing
// changes: each walk steps, as the game does. No game state is written.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cpu.h"
#include "host.h"
#include "gfx.h"
#include "snap_ui_pace.h"

extern GfxStats gfx_counters;   // nvn_api.h; frames: presented frames

// What main+0x9d0de0 reads first: movie[+8] -> owner, owner[+0x38] -> root; a null root returns.
static uint64_t snap_ui_stand_in_owner[8];
static uint64_t snap_ui_stand_in_movie[2] = {0, (uint64_t)(uintptr_t)snap_ui_stand_in_owner};

// The interface runs on the game's main thread; the frame count comes from the presenter.
static SnapUiPace pace = {0, 0, 0, 1};
static uint64_t walks, held_walks, held_movies, stepped_movies, window_ns, frames_seen, frames_held, last_frame;

static int pace_trace(void) {
    static int on = -1;
    if (on < 0) {
        const char *e = getenv("NEWSNAP_UI_PACE_TRACE");
        on = e && !strcmp(e, "1");
    }
    return on;
}

// Before a walk of the movie list: this frame's decision.
void snap_ui_pace_begin(Cpu *c) {
    (void)c;
    uint64_t now = kern_now_ns();
    uint64_t frame = __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED);
    int step = snap_ui_pace_decide(&pace, frame, now, frame_step_cap_ns());
    walks++;
    held_walks += !step;
    if (frame + 1 != last_frame) last_frame = frame + 1, frames_seen++, frames_held += !step;
    if (!pace_trace()) return;
    if (!window_ns) window_ns = now;
    if (now - window_ns < 5000000000ull) return;
    double seconds = (double)(now - window_ns) / 1e9;
    rt_log("snap_ui_pace: %.1f s: %llu frames with the interface, %llu stepped (%.1f steps a second), %llu held; "
           "%llu walks, %llu held; movies stepped %llu, held %llu; frame period %.3f ms",
           seconds, (unsigned long long)frames_seen, (unsigned long long)(frames_seen - frames_held),
           (double)(frames_seen - frames_held) / seconds, (unsigned long long)frames_held,
           (unsigned long long)walks, (unsigned long long)held_walks,
           (unsigned long long)stepped_movies, (unsigned long long)held_movies, (double)frame_step_cap_ns() / 1e6);
    window_ns = now, walks = held_walks = stepped_movies = held_movies = frames_seen = frames_held = 0;
}

// After the loop loaded a movie into x0, right before the original advance call.
void snap_ui_pace_movie(Cpu *c) {
    if (pace.step) {
        stepped_movies++;
        return;
    }
    held_movies++;
    c->x[0] = (uint64_t)(uintptr_t)snap_ui_stand_in_movie;
}
