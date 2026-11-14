// Portable IEEE CRC32 ISA acceleration, configured before guest threads start.
#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
extern int snap_crc32_slice8_on;
extern const uint32_t snap_crc32_slice8_rows[7][256];
void snap_crc32_init(void);
#ifdef __cplusplus
}
#endif
