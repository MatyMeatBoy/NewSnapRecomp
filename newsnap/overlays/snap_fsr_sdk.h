#pragma once
#include <stdint.h>
#include <vulkan/vulkan.h>

/* A provider being present does not establish that Snap supplies temporal inputs. */
typedef struct SnapFsrSdk SnapFsrSdk;
/* Set only from the queried, enabled device feature chain at creation. */
extern int snap_fsr_sdk_int8_enabled;
typedef struct { uint64_t id; char name[192]; } SnapFsrProvider;
typedef struct {
    VkDevice device;
    VkPhysicalDevice physical_device;
    PFN_vkGetDeviceProcAddr get_device_proc;
} SnapFsrDevice;
typedef struct {
    VkImage image;
    VkFormat format;
    VkImageLayout layout;
    VkImageUsageFlags usage;
    uint32_t width, height, samples, layers, mips;
    uint64_t generation;
} SnapFsrImage;
typedef struct {
    uint32_t render_width, render_height, output_width, output_height;
    uint32_t hdr, inverted_depth, infinite_depth, auto_exposure;
    uint64_t generation;
    /* Caller has enabled the SDK-required device features before vkCreateDevice. */
    uint32_t device_contract_verified;
} SnapFsrConfig;
typedef struct {
    VkCommandBuffer command_buffer;
    SnapFsrImage color, depth, motion, exposure, reactive, transparency, output;
    float jitter_x, jitter_y, motion_scale_x, motion_scale_y;
    float delta_ms, pre_exposure, camera_near, camera_far, vertical_fov, meters_factor;
    uint32_t reset;
    /* Set only after scene/HUD boundary, jitter, depth and object motion are verified. */
    uint32_t scene_contract_verified;
} SnapFsrFrame;

SnapFsrSdk *snap_fsr_sdk_open(void);
/* Returns provider count; bounded by capacity; no context allocation or dispatch. */
uint32_t snap_fsr_sdk_query(SnapFsrSdk *, const SnapFsrDevice *, SnapFsrProvider *, uint32_t capacity);
/* Explicit queried provider ID prevents a requested FSR3 context silently becoming FSR4. */
int snap_fsr_sdk_create(SnapFsrSdk *, const SnapFsrDevice *, const SnapFsrConfig *, uint64_t provider_id);
int snap_fsr_sdk_validate(const SnapFsrConfig *, const SnapFsrFrame *);
int snap_fsr_sdk_dispatch(SnapFsrSdk *, const SnapFsrFrame *);
/* Returns 1 only for an actual provider query; zeroed outputs on failure mean unknown. */
int snap_fsr_sdk_memory_usage(SnapFsrSdk *, uint64_t *total, uint64_t *aliasable);
/* Device idle / completed fence is required before closing; caller owns all frame resources. */
void snap_fsr_sdk_close(SnapFsrSdk *);
