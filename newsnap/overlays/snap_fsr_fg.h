// FG-01: AMD FSR frame generation (FidelityFX SDK 2.4 Vulkan provider), off by default.
// One generated frame between two real ones, made into an image of ours and shown by
// the present thread (vk_backend.c), not through FFX's swapchain: the context runs in
// FFX_FRAMEGENERATION_FLAG_NO_SWAPCHAIN_CONTEXT_NOTIFY mode, the way Weeping of the
// Empire (TotK recomp, engine/runtime/nvn/vulkan/ffx.c) uses FSR 3.1 frame generation.
#pragma once
#include <stdint.h>
#include <vulkan/vulkan.h>
#include "snap_fsr_sdk.h"

// AC_FRAME_GEN=fsr (frame_gen in newsnap.ini; default off). Needs the FSR temporal path
// (FSR 3.1 or FSR 4, upscaling or Native AA): its depth, motion vectors and jitter feed it.
int snap_fg_enabled(void);

// In the FSR upscale's command buffer, after its dispatch (snap_fsr_runtime.inc): the
// frame generation prepare for this real frame (render-size depth, motion vectors,
// jitter, camera). output_w/h: the size of the picture that will be presented.
void snap_fg_prepare(VkCommandBuffer cb, const SnapFsrFrame *f, uint32_t render_w, uint32_t render_h,
                     uint32_t output_w, uint32_t output_h);

// Replay thread, when it hands a present to the present thread (vk_backend.c
// present_image): the frameID of the newest prepare not yet taken, 0 for none. It travels
// with the job, so a prepare the replay records for the next frame meanwhile is not used.
uint64_t snap_fg_take(void);
// Present thread: the next present_image generates the frame before frame id.
void snap_fg_arm(uint64_t id);

// gfx_present.c present_image, right after vkBeginCommandBuffer: when armed, dispatches
// the generation with the real picture (src, GENERAL layout) as presentColor and returns
// the generated image (GENERAL layout, same size and format) to blit instead; else 0.
VkImage snap_fg_present_source(VkCommandBuffer cb, VkImage src, VkFormat fmt, int w, int h);

// Present thread: 1 when a generated frame fits the monitor. interval_ns: the real frames'
// measured interval. Like Weeping of the Empire's fg_auto: frame generation only helps while
// the real frames are at most 0.55 of the panel's rate (60 fps needs about 110 Hz or more);
// above that the generated frames would make FIFO wait and slow the game, so only the real
// ones are shown. A change needs 2 s of agreement. Unknown refresh: allowed.
int snap_fg_rate_ok(uint64_t interval_ns);

void snap_fg_release(void);
