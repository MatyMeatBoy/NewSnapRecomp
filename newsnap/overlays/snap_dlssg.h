// FG-DLSS: NVIDIA DLSS frame generation through the raw NGX API (feature 11, nvngx_dlssg.dll), the way NVIDIA's
// "DLSS-FG Programming Guide" (NVIDIA/DLSS v310.9.16, doc/) describes it: the feature writes one interpolated frame
// into an image of ours and "does not handle timing or presentation"; the present thread shows it, as it does for the
// FSR generated frame (snap_fsr_fg.c). The NGX side lives in snap_dlssg.inc, included at the end of vk_dlaa.c, which
// owns the NGX core, its parameter tables and DLSS Super Resolution.
#pragma once
#include <stdint.h>
#include <vulkan/vulkan.h>

typedef struct {
    // NGX's order: row-major for row vectors (the transposes of the runtime's column-vector matrices), no jitter
    float view_to_clip[16], clip_to_view[16], clip_to_prev[16], prev_to_clip[16];
    float pos[3], up[3], right[3], fwd[3], near_z, far_z, fov_y;
} SnapDlssgCamera;

typedef struct { VkImage image; VkImageView view; VkFormat format; uint32_t w, h; } SnapDlssgImage;

typedef struct {
    SnapDlssgImage backbuffer, depth, mv, hudless, out, real;   // hudless.image, real.image 0: none; all in GENERAL layout
    float jitter_x, jitter_y;                              // of the depth, in render pixels
    int reset;
    SnapDlssgCamera cam;
} SnapDlssgFrame;

// Replay thread, right after the DLSS Super Resolution evaluation of the frame: its camera.
void snap_dlssg_camera(SnapDlssgCamera *out);
// Present thread, in its open command buffer: the frame between the previous backbuffer and this one into f->out.
// 1: generated; 0: not available or failed (logged a few times), the caller shows only the real frame.
int snap_dlssg_generate(VkCommandBuffer cb, const SnapDlssgFrame *f);
void snap_dlssg_release(void);
// NGX is not thread-safe: Super Resolution evaluates on the replay thread, frame generation on the present thread.
void snap_ngx_lock(void);
void snap_ngx_unlock(void);
