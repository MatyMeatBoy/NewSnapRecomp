"""GYRO-02: adjustable gyro aiming sensitivity (AC_GYRO_SENS / gyro_sens in the INI).

The owner found gyro aiming slow: "like a 2 in a shooter, should feel like a 5".
The gamepad's rotation rate is scaled before motion_fusion.c integrates it, so the
angular velocity, the integrated angle and the direction the game reads all turn
that much faster than the controller: whichever of them Snap uses, the scale holds.
With a scale other than 1 the gravity pull is left out, since it would turn the
tilt back toward the real one over about two seconds. Default 2.5, range 0.1-10,
live like the mouse sensitivity. Independent of the GPU vendor.
"""

INTEGRATE_BEFORE = '''static void integrate(double R[3][3], const double gyro[3], const double acc[3], double dt) {
    double w[3] = {gyro[0], gyro[1], gyro[2]}, n = norm3(acc);
    if (fabs(n - 1) < 0.15) {'''

INTEGRATE_AFTER = '''static void integrate(double R[3][3], const double gyro[3], const double acc[3], double dt, int pull) {
    double w[3] = {gyro[0], gyro[1], gyro[2]}, n = norm3(acc);
    if (pull && fabs(n - 1) < 0.15) {'''

FEED_BEFORE = '''void motion_feed(MotionFusion *m, const double acc[3], const double gyro[3], uint64_t now) {
    plat_mutex_lock(&m->lock);'''

FEED_AFTER = '''// NewSnap GYRO-02: AC_GYRO_SENS (gyro_sens, default 2.5, 0.1..10, live): the rotation rate is scaled before it is
// integrated, so the rate, the angle and the direction the game reads all turn that much faster than the controller.
// With a scale other than 1 the gravity pull is left out: it would turn the tilt back toward the real one over ~2 s.
static double snap_gyro_scale(void) {
    static double k = -1;
    static unsigned seen;
    unsigned v = cfg_version();
    if (k < 0 || v != seen) {
        double d = cfg_double("AC_GYRO_SENS");
        seen = v, k = !(d >= 0.1) ? 0.1 : d > 10 ? 10 : d;
    }
    return k;
}

void motion_feed(MotionFusion *m, const double acc[3], const double raw_gyro[3], uint64_t now) {
    double k = snap_gyro_scale(), gyro[3] = {raw_gyro[0] * k, raw_gyro[1] * k, raw_gyro[2] * k};
    plat_mutex_lock(&m->lock);'''


def edits():
    return {
        'runtime/motion_fusion.c': [
            ('#include "input.h"\n', '#include "cfg.h"\n#include "input.h"\n'),
            (INTEGRATE_BEFORE, INTEGRATE_AFTER),
            (FEED_BEFORE, FEED_AFTER),
            ('    } else integrate(m->R, gyro, acc, dt);', '    } else integrate(m->R, gyro, acc, dt, k == 1.0);'),
        ],
        'runtime/cfg.c': [
            ('"GPU_PASSES", "HDR",', '"GPU_PASSES", "GYRO_SENS", "HDR",'),
            ('{"MOTION", "input"},', '{"MOTION", "input"}, {"GYRO_SENS", "input"},'),
            ('{"MOTION", "1", "0|1", LIVE},', '{"MOTION", "1", "0|1", LIVE}, {"GYRO_SENS", "2.5", "0.1..10", LIVE},'),
        ],
    }
