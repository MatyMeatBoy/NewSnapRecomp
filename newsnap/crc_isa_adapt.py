"""Portable IEEE CRC32 instruction specialization; donor source stays pristine."""

CRC32_MACRO = '#define CRC32(acc, v, n) simd_crc(simd_crc32_tab, (uint32_t)(acc), (v), n)'

CRC32_SLICE = '''#include "snap_crc.h"
// IEEE reflected CRC, least-significant input byte first. Keep the original
// helper for every other defined width, and for the startup scalar opt-out.
SI uint32_t snap_crc32_instruction(uint32_t acc, uint64_t value, int bytes) {
    if ((bytes == 4 || bytes == 8) && snap_crc32_slice8_on) {
        uint32_t low = (uint32_t)value ^ acc;
        if (bytes == 4)
            return snap_crc32_slice8_rows[2][low & 255] ^
                   snap_crc32_slice8_rows[1][(low >> 8) & 255] ^
                   snap_crc32_slice8_rows[0][(low >> 16) & 255] ^
                   simd_crc32_tab[low >> 24];
        return snap_crc32_slice8_rows[6][low & 255] ^
               snap_crc32_slice8_rows[5][(low >> 8) & 255] ^
               snap_crc32_slice8_rows[4][(low >> 16) & 255] ^
               snap_crc32_slice8_rows[3][low >> 24] ^
               snap_crc32_slice8_rows[2][(value >> 32) & 255] ^
               snap_crc32_slice8_rows[1][(value >> 40) & 255] ^
               snap_crc32_slice8_rows[0][(value >> 48) & 255] ^
               simd_crc32_tab[value >> 56];
    }
    return simd_crc(simd_crc32_tab, acc, value, bytes);
}
#define CRC32(acc, v, n) snap_crc32_instruction((uint32_t)(acc), (v), (n))'''


def edits():
    return {
        'runtime/simd.h': [(CRC32_MACRO, CRC32_SLICE)],
        'runtime/patches.c': [
            ('#include "host.h"', '#include "host.h"\n#include "snap_crc.h"'),
            ('void rt_patches_init(void) {',
             'void rt_patches_init(void) {\n    snap_crc32_init();'),
        ],
    }
