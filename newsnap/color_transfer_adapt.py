"""Preserve Snap's final encoded SDR bytes across Vulkan presentation.

The final source may have an sRGB base format even when the game's last draw
uses a UNORM alias. A Vulkan blit decodes that base format before writing the
UNORM swapchain, darkening the game a second time. Choose a compatible source
view matching the actual destination's transfer class through the existing
identity compute copy. sRGB-only surface fallbacks need the inverse treatment.
No artistic grade changes; floating-point/unknown formats retain old semantics.
"""

ENCODED_FORMAT = '''// Snap final SDR pixels are already display encoded. Colour images in
// vk_texture.c use MUTABLE_FORMAT. Match the source view's transfer class to
// the actual swapchain: neither decode nor encode for UNORM, or decode followed
// by encode for an sRGB-only surface. Matching pairs need no identity copy.
static VkFormat snap_present_encoded_format(VkFormat format, VkFormat destination) {
    int srgb = destination == VK_FORMAT_R8G8B8A8_SRGB || destination == VK_FORMAT_B8G8R8A8_SRGB;
    int unorm = destination == VK_FORMAT_R8G8B8A8_UNORM || destination == VK_FORMAT_B8G8R8A8_UNORM;
    if (!srgb && !unorm) return format;
    if (format == VK_FORMAT_R8G8B8A8_SRGB || format == VK_FORMAT_R8G8B8A8_UNORM)
        return srgb ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    if (format == VK_FORMAT_B8G8R8A8_SRGB || format == VK_FORMAT_B8G8R8A8_UNORM)
        return srgb ? VK_FORMAT_B8G8R8A8_SRGB : VK_FORMAT_B8G8R8A8_UNORM;
    return format;
}

'''


def edits():
    return {'runtime/vk_color.c': [
        ('VkImage vk_color_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, const int crop[4]) {\n'
         '    if (!adjusting()) return VK_NULL_HANDLE;',
         ENCODED_FORMAT +
         'VkImage vk_color_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, VkFormat dstfmt, const int crop[4]) {\n'
         '    int adjust = adjusting();\n'
         '    VkFormat encoded_format = snap_present_encoded_format(fmt, dstfmt);\n'
         '    if (!adjust && encoded_format == fmt) return VK_NULL_HANDLE;\n'
         '    static VkFormat reported = VK_FORMAT_UNDEFINED, reported_dst = VK_FORMAT_UNDEFINED;\n'
         '    if (encoded_format != fmt && (reported != fmt || reported_dst != dstfmt)) {\n'
         '        reported = fmt, reported_dst = dstfmt;\n'
         '        rt_log("vk: final SDR byte transfer: source %d, destination %d, sampled view %d, identity coefficients %d",\n'
         '               (int)fmt, (int)dstfmt, (int)encoded_format, !adjust);\n'
         '    }'),
        ('                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = fmt,',
         '                                .viewType = VK_IMAGE_VIEW_TYPE_2D, .format = encoded_format,'),
    ], 'runtime/vk.h': [
        ('VkImage vk_color_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, const int crop[4]);',
         'VkImage vk_color_record(VkCommandBuffer cb, unsigned slot, VkImage src, VkFormat fmt, VkFormat dstfmt, const int crop[4]);'),
    ], 'runtime/gfx_present.c': [
        ('vk_color_record(cb, slot, src, fmt, rect);',
         'vk_color_record(cb, slot, src, fmt, g_sc_fmt, rect);'),
    ]}
