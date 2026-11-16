// HD-SHADOW-02: the baked shadows of every level, read from the player's own game files when the launcher builds the
// HD shadows mode, without playing first. newsnap/game_textures.py asks for the members of the level archives
// (kinds 1 and 2 in snap_decode.c's requests); after the game's own Oodle decoder, each one comes here:
//
//   kind 1, <shape>^<n>^0^Lightmap.nutexb: the light of a mesh, BC6H signed (.nutexb format 0xd8, NVN 0x4F), one
//           level, 64 to 512 texels. Written as <out>/<hash>.dds, RGBA16F, the file hdshadows.py enlarges, as the
//           runtime's own dump does.
//   kind 2, <shape>^<n>^Shadow.nutexb: the sun shadows painted on a mesh, BC3 sRGB (format 0xa5, NVN 72) with the
//           shadow in alpha, 64 to 2048 texels. Written as <out>/<hash>.png, RGBA8.
//
// For both, the .nutexb footer gives the size, format and data size; the storage bytes are hashed the way the
// runtime hashes the texture when the game uploads it (snap_texpack.c: the same bytes, size and NVN format), so the
// file name matches at load time; the block-linear storage is read with the runtime's own layout code (nvn_tex.c,
// what the upload uses) and the blocks are decoded on the CPU (BC6H: all 14 modes, D3D11 rules).
//
// Nothing here is game data: the pictures are made on the player's PC from the player's files.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "host.h"
#include "nvn_tex.h"
#include "tex.h"
#include "vk.h"

uint64_t snap_texpack_hash(const void *p, uint64_t n, uint32_t w, uint32_t h, int nvn_format);   // snap_texpack.c
void snap_texpack_write_rgba16f(const char *path, const void *px, uint32_t w, uint32_t h);

// ---- BC6H -------------------------------------------------------------------------------------------------------
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

static int unquantize(int x, int n, int sgn) {
    if (!sgn) {
        if (n >= 15) return x;
        if (x == 0) return 0;
        if (x == (1 << n) - 1) return 0xFFFF;
        return ((x << 16) + 0x8000) >> n;
    }
    if (n >= 16) return x;
    int neg = x < 0, u;
    if (neg) x = -x;
    if (x == 0) u = 0;
    else if (x >= (1 << (n - 1)) - 1) u = 0x7FFF;
    else u = ((x << 15) + 0x4000) >> (n - 1);
    return neg ? -u : u;
}

static int sext(int v, int n) { return v & 1 << (n - 1) ? v - (1 << n) : v; }

// One 16-byte block to 16 RGB half floats (rgba: 16 x 4 halves, alpha 1.0); sgn: BC6H_SF16. Returns the mode (1..14),
// 0 if reserved.
int snap_bc6h_block(const uint8_t blk[16], uint16_t out[64], int sgn) {
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
    if (sgn)
        for (int c = 0; c < 3; c++) e[0][c] = sext(e[0][c], nb);
    for (int k = 1; k < 2 * regions; k++)
        for (int c = 0; c < 3; c++) {
            if (md->transformed) e[k][c] = (e[0][c] + sext(e[k][c], md->delta[c])) & mask;
            if (sgn) e[k][c] = sext(e[k][c], nb);
        }
    for (int k = 0; k < 2 * regions; k++)
        for (int c = 0; c < 3; c++) e[k][c] = unquantize(e[k][c], nb, sgn);
    int ib = md->partitioned ? 3 : 4;
    for (int i = 0; i < 16; i++) {
        int region = md->partitioned ? PARTITIONS[shape] >> i & 1 : 0;
        int anchor = i == 0 || (md->partitioned && i == ANCHOR2[shape]);
        int idx = bits(&s, anchor ? ib - 1 : ib);
        int w = md->partitioned ? W3[idx] : W4[idx];
        for (int c = 0; c < 3; c++) {
            int v = (e[2 * region][c] * (64 - w) + e[2 * region + 1][c] * w + 32) >> 6;
            if (!sgn) out[4 * i + c] = (uint16_t)((v * 31) >> 6);
            else out[4 * i + c] = v < 0 ? (uint16_t)(0x8000 | ((-v * 31) >> 5)) : (uint16_t)((v * 31) >> 5);
        }
        out[4 * i + 3] = 0x3C00;
    }
    return mode + 1;
}

// ---- BC3 ------------------------------------------------------------------------------------------------------------
static void bc3_block(const uint8_t blk[16], uint8_t out[64]) {
    int a[8] = {blk[0], blk[1]};
    if (a[0] > a[1]) for (int k = 1; k < 7; k++) a[k + 1] = ((7 - k) * a[0] + k * a[1] + 3) / 7;
    else {
        for (int k = 1; k < 5; k++) a[k + 1] = ((5 - k) * a[0] + k * a[1] + 2) / 5;
        a[6] = 0, a[7] = 255;
    }
    uint64_t ai = 0;
    for (int k = 0; k < 6; k++) ai |= (uint64_t)blk[2 + k] << (8 * k);
    uint32_t c0 = blk[8] | blk[9] << 8, c1 = blk[10] | blk[11] << 8, ci;
    memcpy(&ci, blk + 12, 4);
    int pal[4][3];
    for (int k = 0; k < 2; k++) {
        uint32_t c = k ? c1 : c0;
        int r = c >> 11 & 31, g = c >> 5 & 63, b = c & 31;
        pal[k][0] = r << 3 | r >> 2, pal[k][1] = g << 2 | g >> 4, pal[k][2] = b << 3 | b >> 2;
    }
    for (int c = 0; c < 3; c++) {   // BC3's colour part always has four colours
        pal[2][c] = (2 * pal[0][c] + pal[1][c] + 1) / 3;
        pal[3][c] = (pal[0][c] + 2 * pal[1][c] + 1) / 3;
    }
    for (int i = 0; i < 16; i++) {
        const int *p = pal[ci >> (2 * i) & 3];
        out[4 * i] = (uint8_t)p[0], out[4 * i + 1] = (uint8_t)p[1], out[4 * i + 2] = (uint8_t)p[2];
        out[4 * i + 3] = (uint8_t)a[ai >> (3 * i) & 7];
    }
}

// ---- one decoded .nutexb member --------------------------------------------------------------------------------------
// kind 1 (light map) or 2 (painted shadows). Returns 1 when the picture was written or was there already, 0 when the
// member is not a texture this mode uses, -1 on a malformed file. *hash_out: the runtime's hash of the texture.
int snap_lightmap_export(const uint8_t *raw, size_t size, int kind, const char *dir, uint64_t *hash_out) {
    if (size < 0xB0) return -1;
    const uint8_t *ft = raw + size - 0xB0;
    if (memcmp(ft + 0x40, " XNT", 4) || memcmp(ft + 0xA8, " XET", 4)) return -1;
    uint32_t w, h, depth, mips, layers, data;
    memcpy(&w, ft + 0x84, 4), memcpy(&h, ft + 0x88, 4), memcpy(&depth, ft + 0x8C, 4);
    memcpy(&mips, ft + 0x98, 4), memcpy(&layers, ft + 0xA0, 4), memcpy(&data, ft + 0xA4, 4);
    int light = kind == 1, nvn = light ? 0x4F : 72;   // NVN BC6H_SFLOAT / RGBA_DXT5_SRGB, as the game names them
    if (ft[0x90] != (light ? 0xD8 : 0xA5) || mips != 1 || layers != 1 || depth != 1 || w < 64 || h < 64 || w > 2048 ||
        h > 2048 || w % 4 || h % 4)
        return 0;
    nvn_texdesc d = {.target = 1, .format = nvn, .width = w, .height = h, .depth = 1, .levels = 1};
    nvn_texlayout L;
    nvn_tex_layout(&d, &L);
    uint32_t bw = w / 4, bh = h / 4, row_bytes = bw * 16;
    if (!L.size || L.size > data || data > size - 0xB0) return -1;
    uint64_t hash = snap_texpack_hash(raw, L.size, w, h, nvn);
    if (hash_out) *hash_out = hash;
    char path[2048];
    if (snprintf(path, sizeof path, "%s/%016llx.%s", dir, (unsigned long long)hash, light ? "dds" : "png") >=
        (int)sizeof path)
        return -1;
    FILE *f = fopen(path, "rb");
    if (f) { fclose(f); return 1; }
    uint8_t *blocks = malloc((size_t)row_bytes * bh), *px = malloc((size_t)w * h * (light ? 8 : 4));
    if (!blocks || !px || nvn_deswizzle(&d, 0, 0, raw, blocks, row_bytes)) { free(blocks), free(px); return -1; }
    for (uint32_t by = 0; by < bh; by++)
        for (uint32_t bx = 0; bx < bw; bx++) {
            const uint8_t *blk = blocks + ((size_t)by * bw + bx) * 16;
            if (light) {
                uint16_t texels[64];
                snap_bc6h_block(blk, texels, 1);
                for (int i = 0; i < 16; i++)
                    memcpy(px + ((size_t)(by * 4 + i / 4) * w + bx * 4 + i % 4) * 8, texels + 4 * i, 8);
            } else {
                uint8_t texels[64];
                bc3_block(blk, texels);
                for (int i = 0; i < 16; i++)
                    memcpy(px + ((size_t)(by * 4 + i / 4) * w + bx * 4 + i % 4) * 4, texels + 4 * i, 4);
            }
        }
    if (light) snap_texpack_write_rgba16f(path, px, w, h);
    else {
        char tmp[2060];
        snprintf(tmp, sizeof tmp, "%s.part", path);
        rt_write_png(tmp, px, w, h);
        if (rename(tmp, path)) remove(tmp);
    }
    free(blocks), free(px);
    return 1;
}
