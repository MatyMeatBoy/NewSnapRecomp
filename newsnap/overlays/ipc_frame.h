// Snap's SDK puts the domain header before the CMIF header.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

typedef struct {
    uint32_t command, size;
    const uint8_t *data;
    int domain, close;
} SnapCmif;

static int snap_cmif_frame(const uint8_t *payload, size_t size, int domain, SnapCmif *out) {
    memset(out, 0, sizeof *out);
    if (domain) {
        if (size < 16) return 0;
        uint32_t h[4];
        memcpy(h, payload, 16);
        unsigned kind = h[0] & 255, objects = (h[0] >> 8) & 255, bytes = h[0] >> 16;
        if (h[1] != 1 || objects || bytes > size - 16) return 0; // only the root service, no input objects
        out->domain = 1;
        if (kind == 2 && !bytes) { out->close = 1; return 1; }
        if (kind != 1 || bytes < 16) return 0;
        payload += 16;
        size = bytes;
    }
    if (size < 16) return 0;
    uint32_t cmif[4];
    memcpy(cmif, payload, 16);
    if (cmif[0] != 0x49434653u) return 0;
    out->command = cmif[2];
    out->data = payload + 16;
    out->size = (uint32_t)(size - 16);
    return 1;
}
