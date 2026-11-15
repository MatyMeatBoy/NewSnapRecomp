// ULTRAWIDE-01 (snap_wide.c): replay-thread side of AC_ASPECT=ultrawide.
#pragma once
#include "vk.h"
float snap_wide_k(void);
int snap_wide_pass(VkCommandBuffer cb, const VkTexImage *img, VkFormat view);
int snap_wide_capture(void);
VkImageView snap_wide_capture_view(VkImage image, VkImageView fallback);
void snap_wide_viewport(uint32_t pass_w, VkViewport *v);
void snap_wide_scissor(uint32_t pass_w, VkRect2D *r);
