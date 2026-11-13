"""Keep Snap's own SDR output; ignore donor artistic overrides, including old INIs."""


def edits():
    return {'runtime/cfg.c': [
        ('const char *cfg_value(const char *name) {',
         '#include "snap_neutral.h"\n\nconst char *cfg_value(const char *name) {\n    const char *neutral = snap_neutral_value(name);\n    if (neutral) return neutral;'),
        ('{"SHARPNESS", "80",', '{"SHARPNESS", "0",'),
        ('{"UPSCALER", "fsr",', '{"UPSCALER", "bilinear",'),
        ('{"SHADOW_SCALE", "2",', '{"SHADOW_SCALE", "1",'),
    ], 'runtime/vk_dlaa.c': [
        ('static void sharpen(VkCommandBuffer cb, struct Size *e, VkImage *img, VkImageView *view) {',
         'static void sharpen(VkCommandBuffer cb, struct Size *e, VkImage *img, VkImageView *view) {\n    return; // Snap keeps linear scene light until its own tone-map; no donor pre-HUD RCAS.'),
    ]}
