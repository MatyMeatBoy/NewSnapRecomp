// Capacity query for the host's virtual save mount, measured in logical bytes.
#include <stdio.h>
#include <string.h>
#include "host.h"
#include "ov.h"
#include "fs.h"
#include "snap_metadata.h"
#include "platform/platform.h"

typedef struct { char path[2048]; uint64_t bytes; unsigned depth; int valid; } SnapUsage;

static int usage_entry(const char *name, int kind, uint64_t bytes, void *context) {
    SnapUsage *usage = context;
    if (kind == PLAT_FS_FILE) usage->bytes += bytes;
    else if (kind == PLAT_FS_DIR) {
        SnapUsage child = {.depth = usage->depth + 1, .valid = 1};
        if (child.depth > 32 || snprintf(child.path, sizeof child.path, "%s/%s", usage->path, name) >= (int)sizeof child.path)
            usage->valid = 0;
        else {
            if (plat_fs_list(child.path, usage_entry, &child) != PLAT_FS_OK || !child.valid) usage->valid = 0;
            usage->bytes += child.bytes;
        }
    }
    return 1;
}

static void snap_free_space(Cpu *c) {
    int64_t *out = arg_p(c, 0);
    const char *path = arg_p(c, 1);
    if (!out || !path) { c->x[0] = FS_R_INVALID_ARGUMENT; return; }
    if (!strncmp(path, "sim:", 4)) { *out = 0; c->x[0] = 0; return; }
    if (strncmp(path, "savedata:", 9) && strncmp(path, "save:", 5)) {
        c->x[0] = FS_R_PATH_NOT_FOUND;
        return;
    }
    SnapUsage usage = {.valid = 1};
    if (snprintf(usage.path, sizeof usage.path, "%s/save-tx/work", rt_config()->profile) >= (int)sizeof usage.path
        || plat_fs_list(usage.path, usage_entry, &usage) != PLAT_FS_OK || !usage.valid) {
        c->x[0] = FS_R_INVALID_ARGUMENT;
        return;
    }
    *out = usage.bytes < SNAP_SAVE_SIZE ? (int64_t)(SNAP_SAVE_SIZE - usage.bytes) : 0;
    c->x[0] = 0;
}
HOST_OVERRIDE("_ZN2nn2fs16GetFreeSpaceSizeEPlPKc", snap_free_space);
