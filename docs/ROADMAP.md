# Work after the 0.3 alpha

Implementation and acceptance for these targets now live in the
[0.4 work board](V04.md). The hardware/scene coverage below remains an acceptance
requirement; SDK detection alone is still insufficient.

## Owner targets for v0.4

- FSR 4 with its supported quality presets and automatic compatible model selection,
  including the official INT8 path for RX 6000/7000. No forced model ID guesses.
- FSR 3.1 with its own supported presets and a native/spatial fallback.
- The DLSS Super Resolution integration appropriate to Snap and the detected GPU;
  availability must follow real provider/driver support and the validated inputs.
- Update maintenance from the launcher: detect incompatible private runtime or
  shader/pipeline state, obtain the original build tools when needed, rebuild
  locally from the owner's existing imports, verify and switch outputs only on
  success. Keep saves/configuration and the previous usable runtime recoverable.
  Current 0.3 updates the public launcher and reports private-runtime requirements;
  automated full private recompilation is not implemented yet.

These are implementation targets, not features included in 0.3. Establish the
common Snap temporal-input contract before advertising any of the temporal
backends. SDK/provider detection alone is not a working upscaler.

## Temporal upscaling with broad GPU coverage

The owner requested integration when feasible, after the standalone-launcher
release. Investigate the official AMD FSR SDK 2.4 Vulkan path, with capability-
based selection and a spatial/native alternative. This is not implemented in 0.3.

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
