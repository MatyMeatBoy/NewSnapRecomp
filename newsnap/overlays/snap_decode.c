// Offline decode of archive members using the original decoder from the user's
// hash-verified executable. No proprietary decoder or output is distributed.
//
// Request file (NEWSNAP_OODLE_REQUESTS): <magic, version, count>, then per member <ordinal, stored size, decoded
// size, CRC32, compressed[, kind]> and the stored bytes. Version 1 has no kind (0). Kinds:
//   0  shader archive, written as <output>/<ordinal>.nushdb (newsnap/unpack.py)
//   1  light map and 2 painted shadows of a level (HD-SHADOW-02, snap_lightmap_export.c), written as pictures named
//      by the runtime's texture hash; <output>/export.txt gets one line per member: ordinal, result, hash
//   3  any member as it is, <output>/<ordinal>.bin (tools)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "host.h"
#include "layout.h"
#include "snap_metadata.h"
#include "platform/platform.h"

int snap_lightmap_export(const uint8_t *raw, size_t size, int kind, const char *dir, uint64_t *hash_out);

static void read_exact(FILE *file, void *out, size_t size) {
    if (fread(out, 1, size, file) != size) rt_fatal("shader unpack: truncated request");
}

static uint32_t member_crc(const uint8_t *bytes, size_t size) {
    uint32_t table[256];
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++) c = c >> 1 ^ (c & 1 ? 0xEDB88320u : 0);
        table[i] = c;
    }
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < size; i++) crc = crc >> 8 ^ table[(crc ^ bytes[i]) & 255];
    return crc ^ 0xFFFFFFFFu;
}

void snap_decode_requested(Cpu *c) {
    const char *request = getenv("NEWSNAP_OODLE_REQUESTS");
    if (!request || !*request) return;
    const char *directory = getenv("NEWSNAP_OODLE_OUTPUT");
    if (!directory || !*directory || !SNAP_OODLE_OFFSET)
        rt_fatal("shader unpack: missing output directory or verified decoder mapping");
    FILE *input = fopen(request, "rb");
    if (!input) rt_fatal("shader unpack: cannot open requests");
    uint32_t header[3];
    read_exact(input, header, sizeof header);
    if (header[0] != 0x444F534Eu || (header[1] != 1 && header[1] != 2) || !header[2] || header[2] > 10000)
        rt_fatal("shader unpack: invalid request header");
    FILE *results = NULL;
    for (uint32_t i = 0; i < header[2]; i++) {
        uint32_t r[6] = {0}; // ordinal, stored size, decoded size, member CRC32, compressed, kind (version 2)
        read_exact(input, r, header[1] == 2 ? sizeof r : 5 * sizeof *r);
        if (r[0] != i || !r[1] || !r[2] || r[1] > (64u << 20) || r[2] > (64u << 20) || r[4] > 1 || r[5] > 3)
            rt_fatal("shader unpack: invalid member %u", i);
        uint8_t *packed = calloc(1, (size_t)r[1] + 16), *raw = calloc(1, (size_t)r[2] + 64);
        if (!packed || !raw) rt_fatal("shader unpack: allocation failed");
        read_exact(input, packed, r[1]);
        if (r[4]) {
            uint64_t sp = c->sp;
            c->sp = (sp - 64) & ~15ull;
            memset((void *)(uintptr_t)c->sp, 0, 64);
            ((uint64_t *)(uintptr_t)c->sp)[5] = 3; // OodleLZ_Decode_Unthreaded
            uint64_t got = rt_call(c, MOD_MAIN_BASE + SNAP_OODLE_OFFSET, 8,
                (uint64_t)(uintptr_t)packed, (uint64_t)r[1], (uint64_t)(uintptr_t)raw, (uint64_t)r[2],
                (uint64_t)1, (uint64_t)0, (uint64_t)0, (uint64_t)0);
            c->sp = sp;
            if (got != r[2]) rt_fatal("shader unpack: decoder returned %llu, expected %u for member %u",
                                     (unsigned long long)got, r[2], i);
        } else {
            if (r[1] != r[2]) rt_fatal("shader unpack: invalid raw member size");
            memcpy(raw, packed, r[2]);
        }
        if (member_crc(raw, r[2]) != r[3]) rt_fatal("shader unpack: member %u CRC32 mismatch", i);
        char path[2048];
        if (r[5] == 1 || r[5] == 2) {
            if (!results) {
                if (snprintf(path, sizeof path, "%s/export.txt", directory) >= (int)sizeof path)
                    rt_fatal("shader unpack: output path too long");
                if (!(results = fopen(path, "w"))) rt_fatal("shader unpack: cannot write the export list");
            }
            uint64_t hash = 0;
            int got = snap_lightmap_export(raw, r[2], (int)r[5], directory, &hash);
            fprintf(results, "%u %d %016llx\n", i, got, (unsigned long long)hash);
        } else {
            if (snprintf(path, sizeof path, r[5] == 3 ? "%s/%05u.bin" : "%s/%05u.nushdb", directory, i) >= (int)sizeof path)
                rt_fatal("shader unpack: output path too long");
            if (!plat_file_write_atomic(path, raw, r[2])) rt_fatal("shader unpack: cannot write member %u", i);
        }
        free(raw), free(packed);
        if (!(i % 128) || i + 1 == header[2]) rt_log("shader unpack: %u/%u decoded and CRC32 verified", i + 1, header[2]);
    }
    if (fgetc(input) != EOF) rt_fatal("shader unpack: unexpected request tail");
    fclose(input);
    if (results && fclose(results)) rt_fatal("shader unpack: cannot write the export list");
    rt_log("shader unpack complete: %u verified members", header[2]);
    plat_exit(0);
}
