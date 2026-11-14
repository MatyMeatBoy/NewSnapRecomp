#include "snap_crc.h"
#include "cfg.h"
#include "host.h"
#include <string.h>

// BSS zero preserves scalar operation in probes, which never call patches init.
// Normal boot initializes once on the startup thread, before guest execution.
int snap_crc32_slice8_on;

void snap_crc32_init(void) {
    static int initialized;
    if (initialized) return;
    const char *value = cfg_get("AC_SNAP_CRC32_SLICE8");
    snap_crc32_slice8_on = !value || strcmp(value, "0") != 0;
    initialized = 1;
    rt_log("snap-crc: IEEE CRC32 4/8-byte path: %s",
           snap_crc32_slice8_on ? "slicing-by-eight" : "scalar");
}
