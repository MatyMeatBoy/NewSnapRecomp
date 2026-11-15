"""AA-04: SMAA 1x with Low, Medium, High and Ultra (High by default) before the HUD; see overlays/snap_smaa.c."""


def edits():
    return {
        'runtime/vk_exec.c': [
            ('    vk_dlaa_pass(ex);   // DLAA runs before the bloom chain\'s first pass (vk_dlaa.c)',
             '    { void snap_smaa_pass(VkExec *ex); snap_smaa_pass(ex); }   // AA-04: SMAA before the HUD (snap_smaa.c)\n'
             '    vk_dlaa_pass(ex);   // DLAA runs before the bloom chain\'s first pass (vk_dlaa.c)'),
        ],
        'runtime/cfg.c': [
            ('{"ANTI_ALIASING", "smaa", "off|smaa", LIVE},',
             '{"ANTI_ALIASING", "high", "off|low|medium|high|ultra|smaa", LIVE},'),
        ],
    }
