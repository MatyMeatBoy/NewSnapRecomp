"""Discard camera samples across capture and motion-source discontinuities.

Keep the original input scaling, pad deadzones, axes and fusion algorithm.
The window backend numbers capture transitions because losing and regaining
focus can happen between two guest polls in the same presented frame.
"""

MOTION_POLL = '''// One sensor poll under the input lock. A different/missing source must not
// inherit another controller's orientation or return its recent ring samples.
static void snap_motion_poll(void) {
    static SDL_JoystickID source;
    static int fed;
    float a[3], g[3];
    plat_mutex_lock(&lock);
    int connected = pad && SDL_GamepadConnected(pad);
    SDL_JoystickID id = connected ? SDL_GetGamepadID(pad) : 0;
    if (!input_motion_enabled() || !id) {
        if (connected && sensor_pad == id && sensor_pad) {
            SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_GYRO, false);
            SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_ACCEL, false);
        }
        if (source || sensor_pad) motion_restart(motion_global());
        sensor_pad = 0;
        sensor_ok = 0;
        source = 0;
        fed = 0;
        plat_mutex_unlock(&lock);
        return;
    }
    // scan_pads also clears sensor_pad on a close/reopen between sensor polls.
    if (source != id || sensor_pad != id) {
        motion_restart(motion_global());
        source = id;
        fed = 0;
    }
    SDL_UpdateGamepads();
    int have = sensors_ready() && SDL_GetGamepadSensorData(pad, SDL_SENSOR_ACCEL, a, 3) &&
               SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, g, 3);
    if (have) {
        double acc[3], gyro[3];
        input_motion_axes(a, g, acc, gyro);
        motion_feed(motion_global(), acc, gyro, kern_now_ns());
        fed = 1;
    } else if (fed) {
        motion_restart(motion_global());
        fed = 0;
    }
    plat_mutex_unlock(&lock);
}

static void motion_main(void *arg) {
    (void)arg;
    for (;;) {
        plat_wait_ns(4000000);
        snap_motion_poll();
    }
}'''


def edits():
    return {
        'runtime/input.c': [
            ('''int input_motion_enabled(void) {
    static int on = -1;
    static unsigned seen;
    unsigned v = cfg_version();
    if (on < 0 || v != seen) {
        seen = v;
        on = cfg_bool("AC_MOTION");
    }
    return on;
}''', '''int input_motion_enabled(void) {
    // cfg already publishes live values atomically. A second shared cache here
    // races between the gyro thread and guest six-axis readers.
    return cfg_bool("AC_MOTION");
}'''),
            ('    static uint64_t frame = ~0ull, t0;\n    static int32_t held[2];\n    uint64_t now = plat_now_ns();',
             '    static uint64_t frame = ~0ull, t0;\n    static int32_t held[2];\n'
             '    static uint32_t capture_epoch;\n'
             '    uint64_t now = plat_now_ns();\n'
             '    uint32_t epoch = ikb_capture_epoch();\n'
             '    if (capture_epoch != epoch) {\n'
             '        capture_epoch = epoch;\n'
             '        held[0] = held[1] = 0;\n'
             '        frame = ~0ull;\n'
             '        t0 = now;\n'
             '    }'),
            ('    if (sensor_ok) rt_log("input: motion sensors on (gyro %.0f Hz, accelerometer %.0f Hz)",',
             '    if (!sensor_ok) {\n'
             '        // An accelerometer-enable failure must not leave just the gyro on.\n'
             '        SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_GYRO, false);\n'
             '        SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_ACCEL, false);\n'
             '    }\n'
             '    if (sensor_ok) rt_log("input: motion sensors on (gyro %.0f Hz, accelerometer %.0f Hz)",'),
            ('''static void motion_main(void *arg) {
    (void)arg;
    for (;;) {
        plat_wait_ns(4000000);
        float a[3], g[3];
        int have = 0;
        plat_mutex_lock(&lock);
        if (pad && SDL_GamepadConnected(pad)) {
            SDL_UpdateGamepads();
            have = sensors_ready() && SDL_GetGamepadSensorData(pad, SDL_SENSOR_ACCEL, a, 3) &&
                   SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, g, 3);
        }
        plat_mutex_unlock(&lock);
        if (!have || !input_motion_enabled()) continue;
        double acc[3], gyro[3];
        input_motion_axes(a, g, acc, gyro);
        motion_feed(motion_global(), acc, gyro, kern_now_ns());
    }
}''', MOTION_POLL),
        ],
        'runtime/input_wsys.h': [
            ('int ikb_captured(void);',
             'uint32_t ikb_capture_epoch(void);              // changes on every release/recapture, even between polls\n'
             'int ikb_captured(void);'),
        ],
        'runtime/input_win.c': [
            ('static volatile LONG cur_captured;',
             'static volatile LONG snap_capture_epoch;\nstatic volatile LONG cur_captured;'),
            ('    AcquireSRWLockExclusive(&cur_lock);\n    int want =',
             '    AcquireSRWLockExclusive(&cur_lock);\n    int was_captured = cur_captured != 0;\n    int want ='),
            ('    ReleaseSRWLockExclusive(&cur_lock);',
             '    if (was_captured != (cur_captured != 0)) InterlockedIncrement(&snap_capture_epoch);\n'
             '    ReleaseSRWLockExclusive(&cur_lock);'),
            ('int ikb_captured(void) { return cur_captured != 0; }',
             'uint32_t ikb_capture_epoch(void) { return (uint32_t)InterlockedCompareExchange(&snap_capture_epoch, 0, 0); }\n'
             'int ikb_captured(void) { return cur_captured != 0; }'),
        ],
        'runtime/input_sdl.c': [
            ('static volatile int32_t captured;',
             'static volatile int32_t snap_capture_epoch;\nstatic volatile int32_t captured;'),
            ('    plat_xchg32(&captured, want);',
             '    plat_xchg32(&captured, want);\n    plat_inc32(&snap_capture_epoch);'),
            ('int ikb_captured(void) { return captured != 0; }',
             'uint32_t ikb_capture_epoch(void) { return (uint32_t)plat_cas32(&snap_capture_epoch, 0, 0); }\n'
             'int ikb_captured(void) { return captured != 0; }'),
        ],
    }
