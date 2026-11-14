#pragma once
#include <stdint.h>

enum SnapPresentTraceOp {
    SNAP_PRESENT_ACQUIRE, SNAP_PRESENT_FENCE, SNAP_PRESENT_QUEUE, SNAP_PRESENT_REBUILD,
    SNAP_PRESENT_OP_COUNT
};

/* Set once by the process constructor, before host threads start. Never changed live. */
extern int snap_present_trace_on;
uint64_t plat_now_ns(void);
void snap_present_trace_sample(enum SnapPresentTraceOp, uint64_t start, uint64_t end, int result);

static inline uint64_t snap_present_trace_begin(void) {
    return snap_present_trace_on ? plat_now_ns() : 0;
}
static inline void snap_present_trace_end(enum SnapPresentTraceOp operation, uint64_t start, int result) {
    if (snap_present_trace_on) snap_present_trace_sample(operation, start, plat_now_ns(), result);
}
static inline void snap_present_trace_end_at(enum SnapPresentTraceOp operation, uint64_t start, uint64_t end, int result) {
    if (snap_present_trace_on) snap_present_trace_sample(operation, start, end, result);
}

/* All sampling and metadata calls are serialized by gfx_present.c's existing g_pl. */
void snap_present_trace_modes(const char *requested, const char *effective, uint32_t reported,
                              const uint32_t *modes, uint32_t count, int query_result);
void snap_present_trace_swapchain(uint32_t requested, uint32_t actual, uint32_t width, uint32_t height, int images_result);
