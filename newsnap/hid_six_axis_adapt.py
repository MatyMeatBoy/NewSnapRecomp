"""GYRO-01: answer the IHidServer six-axis commands Snap sends when gyro aiming is on.

The donor's hid service knew only commands 101, 121 and 128; anything else is a
named fatal. Turning on gyro aiming in Snap's options makes the SDK's own hid
client call IsSixAxisSensorAtRest (command 82), which ended the process with
"FATAL: ipc: hid command 82 is not implemented" (owner, RX 6900 XT, 0.7.1 test).
The neighbouring six-axis commands (68-83, switchbrew IHidServer) get the same
treatment so the next one the game reaches does not end it either: setters are
accepted, getters return the SDK defaults, and "at rest" follows the live motion
the gamepad feeds (at rest without it). Sensor states themselves stay with the
existing HOST_OVERRIDE entries in ov_input.c.
"""

BEFORE = '''    default: ipc_unimplemented(s, rq);
    }
}'''

AFTER = '''    // NewSnap GYRO-01: six-axis sensor commands (switchbrew IHidServer 68-83). Setters keep no state: the host feeds
    // fused motion from the gamepad itself (ov_input.c six_fill) and only that reaches the game.
    case 68:   // IsSixAxisSensorFusionEnabled(handle, aruid) -> bool
    case 83: { // IsFirmwareUpdateAvailableForSixAxisSensor(handle, aruid) -> bool
        uint8_t v = rq->cmd == 68;
        IPC_OUT(rs, v);
        return;
    }
    case 71: { // GetSixAxisSensorFusionParameters(handle, aruid) -> (f32 revise power, f32 revise range): SDK defaults
        float v[2] = {0.03f, 0.4f};
        IPC_OUT(rs, v);
        return;
    }
    case 74: { // GetAccelerometerParameters(handle, aruid) -> (f32 x, f32 y): SDK defaults
        float v[2] = {0.0f, 0.0f};
        IPC_OUT(rs, v);
        return;
    }
    case 77:   // GetAccelerometerPlayMode(handle, aruid) -> u32 (0: tight)
    case 80: { // GetGyroscopeZeroDriftMode(handle, aruid) -> u32 (1: standard)
        uint32_t v = rq->cmd == 80;
        IPC_OUT(rs, v);
        return;
    }
    case 82: { // IsSixAxisSensorAtRest(handle, aruid) -> bool: no live motion, or turning slower than ~1.4 degrees/s
        MotionState m;
        uint8_t rest = 1;
        if (input_motion_enabled() && motion_read(motion_global(), &m, 1, kern_now_ns()) == 1)
            rest = m.gyro[0] * m.gyro[0] + m.gyro[1] * m.gyro[1] + m.gyro[2] * m.gyro[2] < 0.004f * 0.004f;   // rev/s
        static int logged;
        if (!logged++) rt_log("hid: IsSixAxisSensorAtRest answered (%s)", rest ? "at rest" : "moving");
        IPC_OUT(rs, rest);
        return;
    }
    case 69: case 70: case 72: case 73: case 75: case 76: case 78: case 79: case 81: {
        // EnableSixAxisSensorFusion, Set/ResetSixAxisSensorFusionParameters, Set/ResetAccelerometerParameters,
        // Set/ResetAccelerometerPlayMode, Set/ResetGyroscopeZeroDriftMode: accepted, nothing to return
        static int logged;
        if (logged < 8) logged++, rt_log("hid: six-axis setting command %u accepted", rq->cmd);
        return;
    }
    default: ipc_unimplemented(s, rq);
    }
}'''


def edits():
    return {'runtime/ov_hid.c': [
        ('#include "ov.h"\n', '#include "ov.h"\n#include "input.h"\n'),
        (BEFORE, AFTER),
    ]}
