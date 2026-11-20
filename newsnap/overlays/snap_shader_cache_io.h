// Regenerable shader metadata only. The existing pipeline autosave thread drains
// owned snapshots; no game inputs, settings, photos or saves use this queue.
#ifndef SNAP_SHADER_CACHE_IO_H
#define SNAP_SHADER_CACHE_IO_H
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "platform/platform.h"

#define SNAP_SHADER_CACHE_LIMIT (8u * 1024u * 1024u)
typedef struct SnapShaderCacheJob {
    struct SnapShaderCacheJob *next;
    size_t size;
    char path[1104];
    unsigned char data[];
} SnapShaderCacheJob;
static PlatMutex snap_shader_queue_lock = PLAT_MUTEX_INIT;
static PlatMutex snap_shader_drain_lock = PLAT_MUTEX_INIT;
static SnapShaderCacheJob *snap_shader_head, *snap_shader_tail;
static size_t snap_shader_bytes;

// Drain lock serializes batches and the rare synchronous fallback. The queue
// lock protects only pointer swaps; a file write never holds the queue lock.
static void snap_shader_cache_drain_locked(void) {
    plat_mutex_lock(&snap_shader_queue_lock);
    SnapShaderCacheJob *job = snap_shader_head;
    snap_shader_head = snap_shader_tail = NULL;
    snap_shader_bytes = 0;
    plat_mutex_unlock(&snap_shader_queue_lock);
    while (job) {
        SnapShaderCacheJob *next = job->next;
        plat_file_write_atomic(job->path, job->data, job->size);
        free(job);
        job = next;
    }
}

static void snap_shader_cache_flush(void) {
    plat_mutex_lock(&snap_shader_drain_lock);
    snap_shader_cache_drain_locked();
    plat_mutex_unlock(&snap_shader_drain_lock);
}

static int snap_shader_cache_write(const char *path, const void *data, size_t size) {
    SnapShaderCacheJob *job = NULL;
    if (size <= SNAP_SHADER_CACHE_LIMIT - sizeof *job && strlen(path) < sizeof job->path)
        job = malloc(sizeof *job + size);
    if (job) {
        job->next = NULL;
        job->size = size;
        strcpy(job->path, path);
        memcpy(job->data, data, size);
        plat_mutex_lock(&snap_shader_queue_lock);
        if (sizeof *job + size <= SNAP_SHADER_CACHE_LIMIT - snap_shader_bytes) {
            if (snap_shader_tail) snap_shader_tail->next = job;
            else snap_shader_head = job;
            snap_shader_tail = job;
            snap_shader_bytes += sizeof *job + size;
            plat_mutex_unlock(&snap_shader_queue_lock);
            return 1;
        }
        plat_mutex_unlock(&snap_shader_queue_lock);
        free(job);
    }
    // Full queue, oversized snapshot or allocation failure: retain the original
    // atomic write behavior, after older snapshots, instead of dropping data.
    plat_mutex_lock(&snap_shader_drain_lock);
    snap_shader_cache_drain_locked();
    int ok = plat_file_write_atomic(path, data, size);
    plat_mutex_unlock(&snap_shader_drain_lock);
    return ok;
}
#endif
