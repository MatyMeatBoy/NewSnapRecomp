// Snap-specific additions to the selected upstream's host service boundary.
#include "host.h"
#include "ov.h"
#include "snap_metadata.h"
#include "nvn_api.h"
#include "platform/platform.h"
#include <stdio.h>
#include <stdlib.h>

// The host account service provides one persistent local account (account_uid).
// Initialize is already replaced by the host; execute this query there too,
// rather than entering an SDK service object that Initialize did not construct.
static void snap_user_count(Cpu *c) {
    int *out = arg_p(c, 0);
    if (!out) rt_fatal("account GetUserCount: null output");
    uint64_t uid[2];
    account_uid(uid);
    *out = 1;
    c->x[0] = 0;
}
HOST_OVERRIDE("_ZN2nn7account12GetUserCountEPi", snap_user_count);

// The virtual save mount is provisioned by fs_host.c on first use. Report the
// capacity declared by this exact dump's control metadata, not Astral Chain's.
static void snap_save_size(Cpu *c) {
    int64_t *data = arg_p(c, 0), *journal = arg_p(c, 1);
    if (data) *data = SNAP_SAVE_SIZE;
    if (journal) *journal = SNAP_JOURNAL_SIZE;
    c->x[0] = 0;
}
HOST_OVERRIDE("_ZN2nn2fs15GetSaveDataSizeEPlS1_RKNS_7account3UidE", snap_save_size);

// Snap asks for TouchScreenState<6>, while upstream only binds <16>.
// The state is a 16-byte header followed by six 40-byte touch records.
static void snap_touch6(Cpu *c) {
    void *out = arg_p(c, 0);
    if (!out) rt_fatal("hid GetTouchScreenState<6>: null output");
    memset(out, 0, 16 + 6 * 40);
    static uint64_t sample;
    uint64_t next = __atomic_add_fetch(&sample, 1, __ATOMIC_RELAXED);
    memcpy(out, &next, sizeof next);
    c->x[0] = 0;
}
HOST_OVERRIDE("_ZN2nn3hid19GetTouchScreenStateILm6EEEvPNS0_16TouchScreenStateIXT_EEE", snap_touch6);

// No touch device is exposed by this host, so there are no gesture samples.
static void snap_gesture_init(Cpu *c) { c->x[0] = 0; }
static void snap_gesture_states(Cpu *c) { c->x[0] = 0; }
HOST_OVERRIDE("_ZN2nn3hid17InitializeGestureEv", snap_gesture_init);
HOST_OVERRIDE("_ZN2nn3hid16GetGestureStatesEPNS0_12GestureStateEi", snap_gesture_states);
static void snap_joy_assignment(Cpu *c) { c->x[0] = 0; } // Dual; the host exposes a full-key pad
HOST_OVERRIDE("_ZN2nn3hid20GetNpadJoyAssignmentERKj", snap_joy_assignment);

// Bring-up currently exposes an offline network interface. No online service is
// advertised; game data paths must continue to handle network unavailability.
static void snap_socket_init(Cpu *c) { c->x[0] = 0x415; } // service unavailable; no socket objects exist
static void snap_network_finalize(Cpu *c) { c->x[0] = 0; }
static void snap_network_available(Cpu *c) { c->x[0] = 0; }
HOST_OVERRIDE("_ZN2nn6socket10InitializeERKNS0_6ConfigE", snap_socket_init);
HOST_OVERRIDE("_ZN2nn6socket8FinalizeEv", snap_network_finalize);
HOST_OVERRIDE("_ZN2nn4nifm18IsNetworkAvailableEv", snap_network_available);
HOST_OVERRIDE("nnsslInitialize", snap_socket_init);

static void snap_crypto_random(Cpu *c) {
    void *out = arg_p(c, 0);
    uint64_t size = arg_x(c, 1);
    if ((!out && size) || size > SIZE_MAX || !plat_random(out, (size_t)size))
        rt_fatal("crypto: host random generation failed");
}
HOST_OVERRIDE("_ZN2nn6crypto36GenerateCryptographicallyRandomBytesEPvm", snap_crypto_random);

// Debug tooling switch used by Snap before device creation. The host has no
// external NVN debugger; nvnDeviceIsExternalDebuggerAttached already returns false.
NVN_API(nvnSetExternalDebuggerEnabledNVX) {
    if (arg_x(c, 0)) rt_log("NVN: external debugger requested; unavailable on the host");
}

// Queries mirror the corresponding MemoryPoolBuilder setters in upstream.
NVN_API(nvnMemoryPoolBuilderGetFlags) { ret_x(c, ((pool_builder_t *)arg_p(c, 0))->flags); }
NVN_API(nvnMemoryPoolBuilderGetSize) { ret_x(c, ((pool_builder_t *)arg_p(c, 0))->size); }
NVN_API(nvnMemoryPoolBuilderGetMemory) { ret_x(c, (uintptr_t)((pool_builder_t *)arg_p(c, 0))->mem); }
NVN_API(nvnMemoryPoolBuilderGetDevice) { ret_x(c, (uintptr_t)((pool_builder_t *)arg_p(c, 0))->dev); }

#define SNAP_MS_QUERY(name, field) \
    NVN_API(name) { ret_x(c, ((ms_st *)arg_p(c, 0))->field); }
SNAP_MS_QUERY(nvnMultisampleStateGetCoverageModulationMode, cov_mod)
SNAP_MS_QUERY(nvnMultisampleStateGetCoverageToColorEnable, cov2color_en)
SNAP_MS_QUERY(nvnMultisampleStateGetCoverageToColorOutput, cov2color_out)
SNAP_MS_QUERY(nvnMultisampleStateGetSampleLocationsEnable, sl_en)
SNAP_MS_QUERY(nvnMultisampleStateGetSampleLocationsGridEnable, sl_grid)
SNAP_MS_QUERY(nvnMultisampleStateGetAlphaToCoverageDither, a2c_dither)

