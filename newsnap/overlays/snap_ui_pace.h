// UI-HZ-01: which game frames run the interface update, 60 a second of real time above 60 fps.
// Pure decision, no guest or host state: the native test drives it directly.
#ifndef SNAP_UI_PACE_H
#define SNAP_UI_PACE_H
#include <stdint.h>

#define SNAP_UI_PACE_STEP_NS 16666667ull          // one interface update as the game paces it
#define SNAP_UI_PACE_SLACK_NS 250000ull            // a frame this close to its step still takes it
#define SNAP_UI_PACE_MAX_DT_NS 100000000ull        // a hitch does not bank steps

typedef struct {
    uint64_t frame;     // presented-frame count of the last decision (+1; 0 before the first)
    uint64_t last_ns;   // host time of the last decision
    uint64_t acc_ns;    // real time not yet turned into a step
    int step;           // the decision in force: 1 update the interface, 0 leave it as it is
} SnapUiPace;

// One decision per presented frame, shared by every interface object of that frame. cap_ns is the
// selected frame period. At 60 fps or below (cap_ns within the slack of one step) every frame steps,
// as the game does. Above it a frame steps when a whole step of real time has accumulated, never
// twice, and a hitch does not bank steps.
static inline int snap_ui_pace_decide(SnapUiPace *p, uint64_t frame, uint64_t now_ns, uint64_t cap_ns) {
    if (p->frame == frame + 1) return p->step;
    int first = !p->frame;
    p->frame = frame + 1;
    if (!cap_ns || cap_ns + SNAP_UI_PACE_SLACK_NS >= SNAP_UI_PACE_STEP_NS || first || now_ns <= p->last_ns) {
        p->last_ns = now_ns;
        p->acc_ns = 0;
        return p->step = 1;
    }
    uint64_t dt = now_ns - p->last_ns;
    p->last_ns = now_ns;
    p->acc_ns += dt > SNAP_UI_PACE_MAX_DT_NS ? SNAP_UI_PACE_MAX_DT_NS : dt;
    if (p->acc_ns + SNAP_UI_PACE_SLACK_NS < SNAP_UI_PACE_STEP_NS) return p->step = 0;
    p->acc_ns = p->acc_ns > SNAP_UI_PACE_STEP_NS ? p->acc_ns - SNAP_UI_PACE_STEP_NS : 0;
    if (p->acc_ns >= SNAP_UI_PACE_STEP_NS) p->acc_ns = SNAP_UI_PACE_STEP_NS - 1;   // one step a frame at most
    return p->step = 1;
}
#endif
