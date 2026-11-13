#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "ipc_frame.h"

int main(void) {
    uint32_t words[16] = {0x00180001, 1, 0, 0, 0x49434653, 0, 1005, 0, 0, 0};
    SnapCmif frame;
    assert(snap_cmif_frame((uint8_t *)words, 40, 1, &frame));
    assert(frame.command == 1005 && frame.size == 8 && frame.domain);
    assert(!snap_cmif_frame((uint8_t *)words, 12, 1, &frame));
    assert(!snap_cmif_frame((uint8_t *)words, 39, 1, &frame));
    words[0] = 0x00180003;
    assert(!snap_cmif_frame((uint8_t *)words, 40, 1, &frame));
    words[0] = 0x49434653;
    words[2] = 77;
    assert(snap_cmif_frame((uint8_t *)words, 16, 0, &frame));
    assert(frame.command == 77 && !frame.domain && frame.size == 0);
    return 0;
}
