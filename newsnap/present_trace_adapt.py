"""Opt-in bounded CPU observations around the donor's actual present operations."""


def edits():
    return {'runtime/gfx_present.c': [
        ('#include "vk.h"', '#include "vk.h"\n#include "snap_present_trace.h"'),
        ('    VkResult r = vkQueuePresentKHR(vk_ctx()->gfx_queue, &pi);\n    vk_queue_unlock();',
         '    uint64_t snap_present_start = snap_present_trace_begin();\n'
         '    VkResult r = vkQueuePresentKHR(vk_ctx()->gfx_queue, &pi);\n'
         '    uint64_t snap_present_end = snap_present_trace_begin();\n'
         '    vk_queue_unlock();\n'
         '    snap_present_trace_end_at(SNAP_PRESENT_QUEUE, snap_present_start, snap_present_end, r);'),
        ('    if (n > 16) n = 16;\n    vkGetPhysicalDeviceSurfacePresentModesKHR(pd, g_surface, &n, m);',
         '    uint32_t snap_modes_reported = n;\n'
         '    if (n > 16) n = 16;\n'
         '    VkResult snap_modes_result = vkGetPhysicalDeviceSurfacePresentModesKHR(pd, g_surface, &n, m);'),
        ('    __atomic_store_n(&g_present_got, name, __ATOMIC_RELEASE);',
         '    __atomic_store_n(&g_present_got, name, __ATOMIC_RELEASE);\n'
         '    if (snap_present_trace_on) {\n'
         '        uint32_t snap_modes[16], snap_count = 0;\n'
         '        if (snap_modes_result == VK_SUCCESS || snap_modes_result == VK_INCOMPLETE) {\n'
         '            snap_count = n < 16 ? n : 16;\n'
         '            for (uint32_t i = 0; i < snap_count; i++) snap_modes[i] = (uint32_t)m[i];\n'
         '        }\n'
         '        snap_present_trace_modes(e, name, snap_modes_reported, snap_modes, snap_count, snap_modes_result);\n'
         '    }'),
        ('static int create_swapchain(void) {', 'static int snap_create_swapchain_impl(void) {'),
        ('    vkGetSwapchainImagesKHR(c->device, g_sc, &g_sc_n, g_sc_img);',
         '    VkResult snap_images_result = vkGetSwapchainImagesKHR(c->device, g_sc, &g_sc_n, g_sc_img);\n'
         '    snap_present_trace_swapchain(count, snap_images_result == VK_SUCCESS ? g_sc_n : 0, ext.width, ext.height, snap_images_result);'),
        ('static void sync_barrier(VkCommandBuffer cb, VkImage img, VkImageLayout from, VkImageLayout to, VkPipelineStageFlags2 s0,',
         'static int create_swapchain(void) {\n'
         '    uint64_t snap_rebuild_start = snap_present_trace_begin();\n'
         '    int snap_rebuild_result = snap_create_swapchain_impl();\n'
         '    snap_present_trace_end(SNAP_PRESENT_REBUILD, snap_rebuild_start, snap_rebuild_result);\n'
         '    return snap_rebuild_result;\n'
         '}\n\n'
         'static void sync_barrier(VkCommandBuffer cb, VkImage img, VkImageLayout from, VkImageLayout to, VkPipelineStageFlags2 s0,'),
        ('    if (vkWaitForFences(c->device, 1, &g_fence[slot], VK_TRUE, 5000000000ull) != VK_SUCCESS) {',
         '    uint64_t snap_fence_start = snap_present_trace_begin();\n'
         '    VkResult snap_fence_result = vkWaitForFences(c->device, 1, &g_fence[slot], VK_TRUE, 5000000000ull);\n'
         '    snap_present_trace_end(SNAP_PRESENT_FENCE, snap_fence_start, snap_fence_result);\n'
         '    if (snap_fence_result != VK_SUCCESS) {'),
        ('    VkResult r = vkAcquireNextImageKHR(c->device, g_sc, 1000000000ull, g_acquire[slot], VK_NULL_HANDLE, &idx);',
         '    uint64_t snap_acquire_start = snap_present_trace_begin();\n'
         '    VkResult r = vkAcquireNextImageKHR(c->device, g_sc, 1000000000ull, g_acquire[slot], VK_NULL_HANDLE, &idx);\n'
         '    snap_present_trace_end(SNAP_PRESENT_ACQUIRE, snap_acquire_start, r);'),
        ('        r = vkAcquireNextImageKHR(c->device, g_sc, 1000000000ull, g_acquire[slot], VK_NULL_HANDLE, &idx);',
         '        snap_acquire_start = snap_present_trace_begin();\n'
         '        r = vkAcquireNextImageKHR(c->device, g_sc, 1000000000ull, g_acquire[slot], VK_NULL_HANDLE, &idx);\n'
         '        snap_present_trace_end(SNAP_PRESENT_ACQUIRE, snap_acquire_start, r);'),
        ('        vkWaitForFences(c->device, 1, &g_fence[slot], VK_TRUE, 5000000000ull);',
         '        uint64_t snap_capture_start = snap_present_trace_begin();\n'
         '        VkResult snap_capture_result = vkWaitForFences(c->device, 1, &g_fence[slot], VK_TRUE, 5000000000ull);\n'
         '        snap_present_trace_end(SNAP_PRESENT_FENCE, snap_capture_start, snap_capture_result);'),
    ]}
