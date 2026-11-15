// HD-SHADOW-02: the light maps of every level, read from the player's own game files when the launcher builds the
// HD shadows mode, without playing first. newsnap/game_textures.py asks for the ^Lightmap.nutexb members of the
// level archives (kind 1 in snap_decode.c's requests); after the game's own Oodle decoder, each one comes here:
//
//   1. The .nutexb footer gives the size, format and data size. Only BC6H unsigned maps (format 0xd8) are light.
//   2. Its storage bytes are hashed the way the runtime hashes the texture when the game uploads it
//      (snap_texpack.c: the same bytes, size and NVN format 79), so the file name matches at load time.
//   3. The block-linear storage (Tegra GOBs, block height from the height as the Switch tools pick it) is read
//      into rows of 4x4 blocks, and the BC6H blocks are decoded on the CPU (all 14 modes, D3D11 BC6H rules).
//   4. <out>/<hash>.dds is written as RGBA16F, the file hdshadows.py enlarges, as the runtime's own dump does.
//
// Nothing here is game data: the pictures are made on the player's PC from the player's files.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "host.h"

uint64_t snap_texpack_hash(const void *p, uint64_t n, uint32_t w, uint32_t h, int nvn_format);   // snap_texpack.c
void snap_texpack_write_rgba16f(const char *path, const void *px, uint32_t w, uint32_t h);

// ---- BC6H (unsigned) ---------------------------------------------------------------------------------------------
// Each mode's fields in stream order: "<endpoint><channel>.<first bit>-<last bit>" reads bits first..last, one per
// stream bit (first > last for the reversed fields of modes 13 and 14). Endpoints: 0 = base, 1 = its pair, 2 and 3 =
// the second region's. Channels r, g, b.
typedef struct { int partitioned, transformed, bits, delta[3]; const char *layout; } Bc6Mode;
static const Bc6Mode MODES[14] = {
    {1, 1, 10, {5, 5, 5}, "g2.4 b2.4 b3.4 r0.0-9 g0.0-9 b0.0-9 r1.0-4 g3.4 g2.0-3 g1.0-4 b3.0 g3.0-3 b1.0-4 b3.1 "
                          "b2.0-3 r2.0-4 b3.2 r3.0-4 b3.3"},
    {1, 1, 7, {6, 6, 6}, "g2.5 g3.4 g3.5 r0.0-6 b3.0 b3.1 b2.4 g0.0-6 b2.5 b3.2 g2.4 b0.0-6 b3.3 b3.5 b3.4 r1.0-5 "
                         "g2.0-3 g1.0-5 g3.0-3 b1.0-5 b2.0-3 r2.0-5 r3.0-5"},
    {1, 1, 11, {5, 4, 4}, "r0.0-9 g0.0-9 b0.0-9 r1.0-4 r0.10 g2.0-3 g1.0-3 g0.10 b3.0 g3.0-3 b1.0-3 b0.10 b3.1 "
                          "b2.0-3 r2.0-4 b3.2 r3.0-4 b3.3"},
    {1, 1, 11, {4, 5, 4}, "r0.0-9 g0.0-9 b0.0-9 r1.0-3 r0.10 g3.4 g2.0-3 g1.0-4 g0.10 g3.0-3 b1.0-3 b0.10 b3.1 "
                          "b2.0-3 r2.0-3 b3.0 b3.2 r3.0-3 g2.4 b3.3"},
    {1, 1, 11, {4, 4, 5}, "r0.0-9 g0.0-9 b0.0-9 r1.0-3 r0.10 b2.4 g2.0-3 g1.0-3 g0.10 b3.0 g3.0-3 b1.0-4 b0.10 "
                          "b2.0-3 r2.0-3 b3.1 b3.2 r3.0-3 b3.4 b3.3"},
    {1, 1, 9, {5, 5, 5}, "r0.0-8 b2.4 g0.0-8 g2.4 b0.0-8 b3.4 r1.0-4 g3.4 g2.0-3 g1.0-4 b3.0 g3.0-3 b1.0-4 b3.1 "
                         "b2.0-3 r2.0-4 b3.2 r3.0-4 b3.3"},
    {1, 1, 8, {6, 5, 5}, "r0.0-7 g3.4 b2.4 g0.0-7 b3.2 g2.4 b0.0-7 b3.3 b3.4 r1.0-5 g2.0-3 g1.0-4 b3.0 g3.0-3 "
                         "b1.0-4 b3.1 b2.0-3 r2.0-5 r3.0-5"},
    {1, 1, 8, {5, 6, 5}, "r0.0-7 b3.0 b2.4 g0.0-7 g2.5 g2.4 b0.0-7 g3.5 b3.4 r1.0-4 g3.4 g2.0-3 g1.0-5 g3.0-3 "
                         "b1.0-4 b3.1 b2.0-3 r2.0-4 b3.2 r3.0-4 b3.3"},
    {1, 1, 8, {5, 5, 6}, "r0.0-7 b3.1 b2.4 g0.0-7 b2.5 g2.4 b0.0-7 b3.5 b3.4 r1.0-4 g3.4 g2.0-3 g1.0-4 b3.0 "
                         "g3.0-3 b1.0-5 b2.0-3 r2.0-4 b3.2 r3.0-4 b3.3"},
    {1, 0, 6, {6, 6, 6}, "r0.0-5 g3.4 b3.0 b3.1 b2.4 g0.0-5 g2.5 b2.5 b3.2 g2.4 b0.0-5 g3.5 b3.3 b3.5 b3.4 r1.0-5 "
                         "g2.0-3 g1.0-5 g3.0-3 b1.0-5 b2.0-3 r2.0-5 r3.0-5"},
    {0, 0, 10, {10, 10, 10}, "r0.0-9 g0.0-9 b0.0-9 r1.0-9 g1.0-9 b1.0-9"},
    {0, 1, 11, {9, 9, 9}, "r0.0-9 g0.0-9 b0.0-9 r1.0-8 r0.10 g1.0-8 g0.10 b1.0-8 b0.10"},
    {0, 1, 12, {8, 8, 8}, "r0.0-9 g0.0-9 b0.0-9 r1.0-7 r0.11-10 g1.0-7 g0.11-10 b1.0-7 b0.11-10"},
    {0, 1, 16, {4, 4, 4}, "r0.0-9 g0.0-9 b0.0-9 r1.0-3 r0.15-10 g1.0-3 g0.15-10 b1.0-3 b0.15-10"},
};
static const uint16_t PARTITIONS[32] = {
    0xCCCC, 0x8888, 0xEEEE, 0xECC8, 0xC880, 0xFEEC, 0xFEC8, 0xEC80, 0xC800, 0xFFEC, 0xFE80, 0xE800, 0xFFE8, 0xFF00,
    0xFFF0, 0xF000, 0xF710, 0x008E, 0x7100, 0x08CE, 0x008C, 0x7310, 0x3100, 0x8CCE, 0x088C, 0x3110, 0x6666, 0x366C,
    0x17E8, 0x0FF0, 0x718E, 0x399C};
static const uint8_t ANCHOR2[32] = {15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
                                    15, 2,  8,  2,  2,  8,  8,  15, 2,  8,  2,  2,  8,  8,  2,  2};
static const int W3[8] = {0, 9, 18, 27, 37, 46, 55, 64};
static const int W4[16] = {0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64};

typedef struct { const uint8_t *b; int pos; } Bits;
static int bit(Bits *s) { int v = s->b[s->pos >> 3] >> (s->pos & 7) & 1; s->pos++; return v; }
static int bits(Bits *s, int n) { int v = 0; for (int i = 0; i < n; i++) v |= bit(s) << i; return v; }

static int unquantize(int x, int n) {
    if (n >= 15) return x;
    if (x == 0) return 0;
    if (x == (1 << n) - 1) return 0xFFFF;
    return ((x << 16) + 0x8000) >> n;
}

static int sext(int v, int n) { return v & 1 << (n - 1) ? v - (1 << n) : v; }

// One 16-byte block to 16 RGB half floats (rgba: 16 x 4 halves, alpha 1.0). Returns the mode (1..14), 0 if reserved.
int snap_bc6h_block(const uint8_t blk[16], uint16_t out[64]) {
    Bits s = {blk, 0};
    int m = bits(&s, 2), mode;
    if (m < 2) mode = m;
    else {
        m |= bits(&s, 3) << 2;
        static const int five[32] = {
            [0x02] = 2, [0x06] = 3, [0x0A] = 4, [0x0E] = 5, [0x12] = 6, [0x16] = 7, [0x1A] = 8, [0x1E] = 9,
            [0x03] = 10, [0x07] = 11, [0x0B] = 12, [0x0F] = 13};
        mode = five[m] ? five[m] : -1;
        if (m == 0x02) mode = 2;
    }
    if (mode < 0) {
        for (int i = 0; i < 16; i++) out[4 * i] = out[4 * i + 1] = out[4 * i + 2] = 0, out[4 * i + 3] = 0x3C00;
        return 0;
    }
    const Bc6Mode *md = &MODES[mode];
    int e[4][3] = {{0}};
    for (const char *p = md->layout; *p;) {
        while (*p == ' ') p++;
        if (!*p) break;
        int c = *p == 'r' ? 0 : *p == 'g' ? 1 : 2;
        int ep = p[1] - '0';
        p += 3;   // past "r0."
        int first = (int)strtol(p, (char **)&p, 10), last = first;
        if (*p == '-') p++, last = (int)strtol(p, (char **)&p, 10);
        int step = last >= first ? 1 : -1;
        for (int b = first;; b += step) {
            e[ep][c] |= bit(&s) << b;
            if (b == last) break;
        }
    }
    int regions = md->partitioned ? 2 : 1, shape = md->partitioned ? bits(&s, 5) : 0;
    int nb = md->bits, mask = (1 << nb) - 1;
    if (md->transformed)
        for (int k = 1; k < 2 * regions; k++)
            for (int c = 0; c < 3; c++) e[k][c] = (e[0][c] + sext(e[k][c], md->delta[c])) & mask;
    for (int k = 0; k < 2 * regions; k++)
        for (int c = 0; c < 3; c++) e[k][c] = unquantize(e[k][c], nb);
    int ib = md->partitioned ? 3 : 4;
    for (int i = 0; i < 16; i++) {
        int region = md->partitioned ? PARTITIONS[shape] >> i & 1 : 0;
        int anchor = i == 0 || (md->partitioned && i == ANCHOR2[shape]);
        int idx = bits(&s, anchor ? ib - 1 : ib);
        int w = md->partitioned ? W3[idx] : W4[idx];
        for (int c = 0; c < 3; c++) {
            int v = (e[2 * region][c] * (64 - w) + e[2 * region + 1][c] * w + 32) >> 6;
            out[4 * i + c] = (uint16_t)((v * 31) >> 6);
        }
        out[4 * i + 3] = 0x3C00;
    }
    return mode + 1;
}

// ---- block-linear storage ------------------------------------------------------------------------------------------
// Byte offset of (x bytes, y rows) in a Tegra block-linear surface of row_bytes per row and block height bh GOBs.
static size_t bl_offset(uint32_t x, uint32_t y, uint32_t row_bytes, uint32_t bh) {
    uint32_t gobs_x = (row_bytes + 63) / 64;
    size_t block = (size_t)(y / (8 * bh)) * gobs_x + x / 64;
    size_t off = block * 512 * bh + (y % (8 * bh) / 8) * 512;
    return off + (x % 64 / 32) * 256 + (y % 8 / 2) * 64 + (x % 32 / 16) * 32 + (y % 2) * 16 + x % 16;
}

static uint32_t block_height(uint32_t rows) {   // GOBs per block: the Switch default for a level of this many rows
    uint32_t bh = 16;
    while (bh > 1 && rows <= (bh / 2) * 8) bh /= 2;
    return bh;
}

// One decoded .nutexb member (kind 1). Returns 1 when a light map was written or was there already, 0 when the
// member is not a light map this mode uses, -1 on a malformed file.
int snap_lightmap_export(const uint8_t *raw, size_t size, const char *dir, uint64_t *hash_out, int *modes) {
    if (size < 0xB0) return -1;
    const uint8_t *ft = raw + size - 0xB0;
    if (memcmp(ft + 0x40, " XNT", 4) || memcmp(ft + 0xA8, " XET", 4)) return -1;
    uint32_t w, h, depth, mips, layers, data;
    memcpy(&w, ft + 0x84, 4), memcpy(&h, ft + 0x88, 4), memcpy(&depth, ft + 0x8C, 4);
    memcpy(&mips, ft + 0x98, 4), memcpy(&layers, ft + 0xA0, 4), memcpy(&data, ft + 0xA4, 4);
    if (ft[0x90] != 0xD8 || mips != 1 || layers != 1 || depth != 1 || w < 64 || h < 64 || w > 2048 || h > 2048 ||
        w % 4 || h % 4)
        return 0;
    uint32_t bw = w / 4, bh = h / 4, row_bytes = bw * 16;
    if (data > size - 0xB0 || data < (size_t)row_bytes * bh) return -1;
    uint64_t hash = snap_texpack_hash(raw, data, w, h, 79);   // NVN BC6H_UFLOAT, as the game names it
    if (hash_out) *hash_out = hash;
    char path[2048];
    if (snprintf(path, sizeof path, "%s/%016llx.dds", dir, (unsigned long long)hash) >= (int)sizeof path) return -1;
    FILE *f = fopen(path, "rb");
    if (f) { fclose(f); return 1; }
    uint16_t *px = malloc((size_t)w * h * 8);
    if (!px) return -1;
    uint32_t gob_h = block_height(bh);
    for (uint32_t by = 0; by < bh; by++)
        for (uint32_t bx = 0; bx < bw; bx++) {
            size_t off = bl_offset(bx * 16, by, row_bytes, gob_h);
            if (off + 16 > data) { free(px); return -1; }
            uint16_t texels[64];
            int mode = snap_bc6h_block(raw + off, texels);
            if (modes) modes[mode]++;
            for (int i = 0; i < 16; i++)
                memcpy(px + ((size_t)(by * 4 + i / 4) * w + bx * 4 + i % 4) * 4, texels + 4 * i, 8);
        }
    snap_texpack_write_rgba16f(path, px, w, h);
    free(px);
    return 1;
}
