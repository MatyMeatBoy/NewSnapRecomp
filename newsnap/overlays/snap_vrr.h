#pragma once
#include <stddef.h>
#include <stdint.h>
#include <vulkan/vulkan.h>

enum SnapRefreshState { SNAP_REFRESH_UNKNOWN, SNAP_REFRESH_FIXED, SNAP_REFRESH_VARIABLE };
typedef struct {
    uint64_t generation, observed_ns, refresh_duration_ns, refresh_interval_ns;
    uint32_t process_id;
    int timing_api_available;
    VkResult result;
    enum SnapRefreshState presentation;
    char reason[48], monitor_id[96], monitor_name[192], present_mode[24];
} SnapVrrStatus;

void snap_vrr_reset(SnapVrrStatus *, uint64_t generation, uint64_t now, const char *reason);
void snap_vrr_apply_result(SnapVrrStatus *, VkResult result, uint64_t duration, uint64_t interval, uint64_t now);
/* Returns bytes excluding NUL, or 0 on insufficient capacity (never truncated JSON). */
size_t snap_vrr_json(const SnapVrrStatus *, char *output, size_t capacity);
int snap_vrr_append_extension(const char **names, uint32_t *count, uint32_t capacity, const char *name);
int snap_vrr_extension_bundle(const VkExtensionProperties *, uint32_t count);
extern int snap_vrr_instance_capabilities;

/* All runtime functions below run under the present lock, except initialization before presents. */
void snap_vrr_device_ready(VkDevice, int enabled);
void snap_vrr_swapchain_changed(VkSwapchainKHR, const char *actual_present_mode);
void snap_vrr_after_present(VkDevice, VkSwapchainKHR, VkResult present_result);
void snap_vrr_shutdown(void);
