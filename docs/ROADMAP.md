# Work after the 0.2 alpha

## Temporal upscaling with broad GPU coverage

The owner requested integration when feasible, after the standalone-launcher
release. Investigate the official AMD FSR SDK 2.4 Vulkan path, with capability-
based selection and a spatial/native alternative. This is not implemented in 0.2.

AMD's October 28, 2026 announcement documents Vulkan support and INT8 models
for RX 6000/7000 and selected integrated GPUs:
[official SDK update](https://gpuopen.com/learn/amd-fsr-sdk-2-4-rx-6000-ryzen-apus/).
Those hardware/model claims belong to AMD; they do not establish Snap integration
or testing on our hardware. Preserve licenses and use official SDK distributions.

Before enabling a temporal upscaler, establish Snap's scene color/depth identity,
camera matrices and jitter, motion vectors and their units, exposure, history
reset at cuts/loading/photo transitions, transparent/reactive inputs and the
native HUD/photo boundary. Validate static detail, moving Pokémon, vegetation,
particles, occlusion, zoom and shutter timing at several resolutions. Compare
photographic evaluation and saved images; an FPS counter alone is insufficient.

Keep an explicit matrix of supported APIs, GPU capabilities, model actually
selected, memory cost and measured results on AMD and NVIDIA. Never silently
enable donor camera/buffer offsets. Devices outside the ML path retain the
spatial/bilinear option if they meet the renderer's independent Vulkan minimums.

## Remaining gameplay acceptance

- Complete a route, evaluate a photo and validate saved-photo reload/export.
- Broaden session, camera, audio and scene-transition regressions.
- Identify geometry-stage consumers currently unsupported by the translator.
- Extend supersampling to handheld only after its resource-registration contract
  is adapted and image/photo correctness is established.
- Investigate simulation/presentation separation above 60 FPS; keep the current
  native timing until equivalence checks pass.
