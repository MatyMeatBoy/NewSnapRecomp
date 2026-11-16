// MENU-FPS-01: interface motion drawn between two interface steps above 60 fps.
//
// The interface's logic and timelines step 60 times a second (UI-HZ-01), so everything they move stands still on
// the frames in between. The interface player hands each thing it draws (shape, text) its matrix on screen right
// before drawing it. For a matrix that changed on two interface steps in a row (something in motion), the frames
// after a step are drawn on the way from the matrix of the step before to the new one, by the real time since the
// step: the motion is drawn one interface step (16.7 ms) late and on every frame. Only what is handed to the
// renderer changes; the player's own matrices, which the interface logic reads, are never touched.
//
// Left as the game hands them: a matrix seen for the first time (nothing to come from: no ghost of a clip that just
// appeared), the first step of a motion and a step that does not continue the last one (a jump: a looping animation
// starting over, a row reused for another entry), matrices that change on frames that do not step (clips of an
// interface object that runs on every frame), and everything under a clip the game itself places on every frame
// (`live`: the pointer, the reticle, the brackets over a subject), which is already drawn where the game asks.
//
// Pure table logic, no guest or host state: the native test drives it directly.
#ifndef SNAP_UI_MOTION_H
#define SNAP_UI_MOTION_H
#include <stdint.h>
#include <string.h>

#define SNAP_UI_MOTION_SLOTS 8192            // a power of two; a screen draws a few hundred to a few thousand things
#define SNAP_UI_MOTION_PROBES 16
#define SNAP_UI_MOTION_LIVE_FRAMES 60        // how long a matrix that changed off-step is left alone

typedef struct {
    uint64_t key;            // address of the matrix in the player (identity of the thing drawn)
    uint64_t frame;          // game frame it was last handed over
    uint64_t change_step;    // interface step of its last change (0: none yet)
    float now[6], before[6]; // the matrix as of the last step, and as of the step before it
    float out[6];            // what was handed to the renderer in its place
    uint32_t live;           // frames left during which it is left alone
    uint8_t blend;           // the last change continues a motion
    uint8_t handed;          // `out` was handed over in this frame
} SnapUiMotionEntry;

typedef struct {
    SnapUiMotionEntry slot[SNAP_UI_MOTION_SLOTS];
} SnapUiMotion;

static inline float snap_ui_motion_size(const float *a, const float *b, int from, int to) {
    float size = 0;
    for (int i = from; i < to; i++) {
        float d = a[i] - b[i];
        size += d < 0 ? -d : d;
    }
    return size;
}

// A change continues the motion of the step before when it is not much larger than that one: an animation easing in
// at most doubles its step, and a jump is many times the motion it interrupts. Scale and rotation (the first four
// terms) and position (the last two, in pixels) are compared separately.
static inline int snap_ui_motion_continues(const float *before, const float *now, const float *next) {
    float turn_last = snap_ui_motion_size(now, before, 0, 4), turn = snap_ui_motion_size(next, now, 0, 4);
    float move_last = snap_ui_motion_size(now, before, 4, 6), move = snap_ui_motion_size(next, now, 4, 6);
    return turn <= 4.0f * turn_last + 0.01f && move <= 4.0f * move_last + 1.0f;
}

// The matrix to hand to the renderer for `key`, whose matrix in the player is `matrix` (six floats): `matrix` itself
// or the entry's `out`. frame: the game frame; step: the count of interface steps so far, the one of this frame
// included; stepped: this frame steps; phase: the real time since the step's due time over one step, 0..1; live: the
// thing belongs to a clip the game places on every frame.
static inline const float *snap_ui_motion_matrix(SnapUiMotion *m, uint64_t key, const float *matrix, uint64_t frame,
                                                 uint64_t step, int stepped, float phase, int live) {
    uint64_t hash = (key >> 3) * 0x9e3779b97f4a7c15ull;
    SnapUiMotionEntry *e = NULL, *spare = NULL;
    for (unsigned probe = 0; probe < SNAP_UI_MOTION_PROBES; probe++) {
        SnapUiMotionEntry *s = &m->slot[(hash >> 40) + probe & (SNAP_UI_MOTION_SLOTS - 1)];
        if (s->key == key) { e = s; break; }
        if (!spare && (!s->key || s->frame + 2 < frame)) spare = s;   // free, or not drawn for two frames
    }
    if (!e) {
        if (!spare) return matrix;   // table crowded here: as the game hands it
        e = spare;
        memset(e, 0, sizeof *e);
        e->key = key;
        e->frame = frame;
        memcpy(e->now, matrix, sizeof e->now);
        memcpy(e->before, matrix, sizeof e->before);
        return matrix;
    }
    if (e->frame == frame) {   // handed over again in the same frame (a shape in several parts): the same answer
        return e->handed && !memcmp(matrix, e->now, sizeof e->now) ? e->out : matrix;
    }
    int drawn_last_frame = e->frame + 1 == frame;
    e->frame = frame;
    e->handed = 0;
    if (e->live) e->live--;
    if (live) e->live = SNAP_UI_MOTION_LIVE_FRAMES;
    if (!drawn_last_frame) {   // back after a pause: nothing to come from
        memcpy(e->now, matrix, sizeof e->now);
        memcpy(e->before, matrix, sizeof e->before);
        e->change_step = 0, e->blend = 0;
        return matrix;
    }
    if (memcmp(matrix, e->now, sizeof e->now)) {
        if (!stepped) {   // moved on a frame that does not step: something drives it on every frame
            e->live = SNAP_UI_MOTION_LIVE_FRAMES;
            e->blend = 0, e->change_step = 0;
            memcpy(e->before, matrix, sizeof e->before);
        } else {
            e->blend = e->change_step && e->change_step + 1 == step && snap_ui_motion_continues(e->before, e->now, matrix);
            e->change_step = step;
            memcpy(e->before, e->now, sizeof e->before);
        }
        memcpy(e->now, matrix, sizeof e->now);
    }
    if (!e->blend || e->live || e->change_step != step) return matrix;
    if (phase < 0) phase = 0;
    if (phase >= 1) return matrix;
    for (int i = 0; i < 6; i++) e->out[i] = e->before[i] + (e->now[i] - e->before[i]) * phase;
    e->handed = 1;
    return e->out;
}
#endif
