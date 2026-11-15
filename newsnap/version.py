"""Identity of the current development candidate; published artifacts stay immutable."""
VERSION = '0.9.8'
RUNTIME_API = 3
RUNTIME_CAPABILITIES = ('launcher-restart75', 'native-render-levels',
                        'docked-supersampling', 'controller-db', 'guest-jumps',
                        'snap-temporal-camera', 'official-fsr-vulkan', 'neutral-sdr-output',
                        'ieee-crc-slicing8', 'high-fps-presets', 'display-frame-rate', 'hd-photo-thumbnails', 'fg-hudless', 'ultrawide', 'texpack', 'snap-menu', 'ui-pace', 'pad-pace', 'hd-shadows', 'texpack-save')

# Raise when a change alters translated shaders or their pipelines (translator patches, SPIR-V rewrites,
# shader-visible runtime state). An update with the same SHADER_EPOCH and translator keeps the
# player's compiled shader cache and preparation (maintenance.replace_runtime).
SHADER_EPOCH = 1
