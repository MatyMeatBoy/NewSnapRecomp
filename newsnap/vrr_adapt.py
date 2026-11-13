"""Status-only Vulkan presentation timing; no queues, schedules or sync policy changes."""


def edits():
    return {'runtime/vk_device.c': [
        ('#include "vk.h"', '#include "vk.h"\n#include "snap_vrr.h"'),
        ('    vk_xess_instance_exts(ext, &n_ext, 24);', '''    vk_xess_instance_exts(ext, &n_ext, 24);
    snap_vrr_instance_capabilities = instance_ext_present(VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME) &&
        snap_vrr_append_extension(ext, &n_ext, 24, VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME);'''),
        ('} FeatureChain;', '''#if defined(VK_EXT_present_timing) && defined(VK_KHR_present_id2)
    VkPhysicalDevicePresentTimingFeaturesEXT snap_present_timing;
    VkPhysicalDevicePresentId2FeaturesKHR snap_present_id;
#endif
} FeatureChain;'''),
        ('    // Graphics pipeline library: chained last so it can be dropped again when vk_caps_gpl declines it.', '''    int snap_vrr_negotiated = 0;
#if defined(VK_EXT_present_timing) && defined(VK_KHR_present_id2)
    // Exact EXT dependencies: swapchain, present_id2, calibrated_timestamps, instance capabilities2.
    if (n_ext <= 75 && snap_vrr_extension_bundle(ep, ne)) { // reserve three dependencies and two GPL slots
        snap_vrr_append_extension(ext, &n_ext, 80, VK_EXT_PRESENT_TIMING_EXTENSION_NAME);
        snap_vrr_append_extension(ext, &n_ext, 80, VK_KHR_PRESENT_ID_2_EXTENSION_NAME);
        snap_vrr_append_extension(ext, &n_ext, 80, VK_KHR_CALIBRATED_TIMESTAMPS_EXTENSION_NAME);
        CHAIN(snap_present_timing, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_TIMING_FEATURES_EXT);
        CHAIN(snap_present_id, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_ID_2_FEATURES_KHR);
        snap_vrr_negotiated = 1;
    }
#endif
    // Graphics pipeline library: chained last so it can be dropped again when vk_caps_gpl declines it.'''),
        ('    vk_caps_driver(g_vk.phys);', '''#if defined(VK_EXT_present_timing) && defined(VK_KHR_present_id2)
    snap_vrr_negotiated = snap_vrr_negotiated && c->snap_present_timing.presentTiming;
    // Status queries need no absolute/relative scheduling features and emit no present IDs.
    c->snap_present_timing.presentAtAbsoluteTime = VK_FALSE;
    c->snap_present_timing.presentAtRelativeTime = VK_FALSE;
    c->snap_present_id.presentId2 = VK_FALSE;
#endif
    vk_caps_driver(g_vk.phys);'''),
        ('    vkGetDeviceQueue(g_vk.device, g_vk.gfx_family, 0, &g_vk.gfx_queue);',
         '    snap_vrr_device_ready(g_vk.device, snap_vrr_negotiated);\n    vkGetDeviceQueue(g_vk.device, g_vk.gfx_family, 0, &g_vk.gfx_queue);'),
    ], 'runtime/gfx_present.c': [
        ('#include "vk.h"', '#include "vk.h"\n#include "snap_vrr.h"'),
        ('    vk_device_fault_report(r);\n    if (r == VK_ERROR_OUT_OF_DATE_KHR',
         '    snap_vrr_after_present(vk_ctx()->device, g_sc, r); // g_pl held: serialize against swapchain destruction\n    vk_device_fault_report(r);\n    if (r == VK_ERROR_OUT_OF_DATE_KHR'),
        ('    if (old) vkDestroySwapchainKHR(c->device, old, NULL);',
         '    snap_vrr_swapchain_changed(g_sc, gfx_window_present_mode());\n    if (old) vkDestroySwapchainKHR(c->device, old, NULL);'),
        ('        if (g_sc) vkDestroySwapchainKHR(c->device, g_sc, NULL);',
         '        snap_vrr_shutdown();\n        if (g_sc) vkDestroySwapchainKHR(c->device, g_sc, NULL);'),
    ]}
