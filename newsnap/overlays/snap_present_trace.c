/* Diagnostic CPU-call durations only. No Vulkan queries, locks, scheduling or policy changes. */
#include "snap_present_trace.h"
#include "host.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int snap_present_trace_on;
__attribute__((constructor)) static void snap_present_trace_init(void) {
    const char *value = getenv("AC_SNAP_PRESENT_TRACE");
    snap_present_trace_on = value && !strcmp(value, "1");
}

typedef struct {
    uint64_t count, sum, min, max, other, last_report_ns, last_report_count;
} TraceBucket;
static TraceBucket buckets[SNAP_PRESENT_OP_COUNT];
static const char *const names[] = {"acquire", "fence", "queue_present", "rebuild"};

void snap_present_trace_sample(enum SnapPresentTraceOp operation, uint64_t start, uint64_t end, int result) {
    if (!snap_present_trace_on || (unsigned)operation >= SNAP_PRESENT_OP_COUNT) return;
    TraceBucket *bucket = &buckets[operation];
    uint64_t duration = end >= start ? end - start : 0;
    if (!bucket->count || duration < bucket->min) bucket->min = duration;
    if (duration > bucket->max) bucket->max = duration;
    bucket->sum += duration;
    bucket->count++;
    /* Rebuild returns the original function's boolean, Vulkan calls return VkResult. */
    bucket->other += operation == SNAP_PRESENT_REBUILD ? result != 1 : result != 0;
    int elapsed = end >= bucket->last_report_ns && end - bucket->last_report_ns >= 1000000000ull;
    if (bucket->count != 1 && (!elapsed ||
            (operation != SNAP_PRESENT_REBUILD && bucket->count - bucket->last_report_count < 120))) return;
    bucket->last_report_ns = end;
    bucket->last_report_count = bucket->count == 1 ? 0 : bucket->count;
    rt_log("snap_present_trace: operation=%s count=%llu sum_ns=%llu min_ns=%llu max_ns=%llu other_results=%llu last_result=%d cumulative=1",
           names[operation], (unsigned long long)bucket->count, (unsigned long long)bucket->sum,
           (unsigned long long)bucket->min, (unsigned long long)bucket->max,
           (unsigned long long)bucket->other, result);
}

static struct {
    char requested[24], effective[24], modes[192];
    uint32_t reported, captured;
    int query_result, emitted;
    uint64_t last_report_ns;
} metadata;

void snap_present_trace_modes(const char *requested, const char *effective, uint32_t reported,
                              const uint32_t *modes, uint32_t count, int query_result) {
    if (!snap_present_trace_on) return;
    snprintf(metadata.requested, sizeof metadata.requested, "%s", requested ? requested : "");
    snprintf(metadata.effective, sizeof metadata.effective, "%s", effective ? effective : "");
    metadata.reported = reported;
    metadata.captured = count < 16 ? count : 16;
    metadata.query_result = query_result;
    metadata.modes[0] = 0;
    size_t used = 0;
    if (!modes) metadata.captured = 0;
    for (uint32_t i = 0; i < metadata.captured; i++)
        used += (size_t)snprintf(metadata.modes + used, sizeof metadata.modes - used, "%s%u", i ? "," : "", modes[i]);
}

void snap_present_trace_swapchain(uint32_t requested, uint32_t actual, uint32_t width, uint32_t height, int images_result) {
    if (!snap_present_trace_on) return;
    uint64_t now = plat_now_ns();
    if (metadata.emitted && (now < metadata.last_report_ns || now - metadata.last_report_ns < 1000000000ull)) return;
    metadata.emitted = 1;
    metadata.last_report_ns = now;
    rt_log("snap_present_trace: swapchain requested=%s effective=%s enumerated=%s modes_reported=%u modes_captured=%u modes_query_result=%d images_requested=%u images_actual=%u images_query_result=%d extent=%ux%u",
           metadata.requested, metadata.effective, metadata.modes, metadata.reported, metadata.captured,
           metadata.query_result, requested, actual, images_result, width, height);
}
