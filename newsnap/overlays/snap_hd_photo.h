// SS-03: photo thumbnails shown from a full-resolution copy (snap_hd_photo.c).
#pragma once
#include <stdint.h>
#include "vk.h"
int snap_hd_photo_on(void);
uint32_t snap_hd_photo_gen(void);
void snap_hd_photo_pass(VkCommandBuffer cb, const VkTexImage *img);
VkImageView snap_hd_photo_view(VkImage bc, VkImageView fallback);
void snap_hd_photo_gone(VkImage bc);
