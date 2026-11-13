# Video compatibility in Snap

The runtime donor remains Astral Chain 1.14, commit
`248e0b29f308ca84a2d2092019cc60e7fc50ae85`. Its game instruction patches,
camera layouts and post-processing recognizers are not Snap contracts.

| Setting | Snap implementation and limits |
| --- | --- |
| Window / fullscreen | Host window and Vulkan swapchain; fullscreen follows the monitor. |
| FIFO / mailbox / immediate / FIFO relaxed | Real Vulkan presentation mode, with FIFO fallback when unavailable. Does not itself change guest simulation speed. |
| VRR | No dedicated VRR detection or activation; the selected presentation mode does not prove VRR is active. |
| FSR 1 / bilinear | Final presentation scaling. Includes the game's HUD. Does not reduce the original 3D rendering workload. |
| Sharpness | RCAS with FSR presentation, including 1:1 output. |
| SDR color | Final image color adjustment. |
| Explicit anisotropy | Vulkan material sampler filtering; automatic donor resolution heuristics are not a verified Snap resolution signal. |
| Render scale | Snap's native engine levels: game, 50, 60, 70, 80, 90, 100. Native-helper tests and initial 3D GPU probes below; photographic acceptance remains required. |
| Output size | Native docked 1920×1080 / handheld 1280×720 selected by operation mode. Arbitrary output sizes and larger budgets are not implemented by this render patch. |
| DLSS / XeSS / temporal FSR 3 | Backend code exists, but Snap scene/camera/jitter/motion-vector integration is unverified. |
| HDR / donor AO / PCSS / shadow scale | Donor-specific recognizers or resource rules; not established as Snap features. |

## Verified render-level boundary

The patch applies only to main build ID
`ddb900ff04a912ed42430508389853cfaf1accce`, original NSO SHA256
`ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443`.
The generator verifies instruction `b94ce808` at module offset `0x5cc0b0`.
It calls `snap_render_select(Cpu *)`, then executes the original
`ldr w8,[x0,#0xce8]`. No instruction address comes from another game.

At this point x0 is the renderer object. Offset `0xce8` holds native level
0..5; offset `0xcec` holds mode 0=docked / 1=handheld. The helper changes only
the level after checking the eight-byte field span is writable guest memory.
All CPU registers and flags remain untouched. `game` performs no guest reads
or writes unless diagnostic tracing is explicitly requested. Unsupported
values, including 25, 75 and 150, log one rejection and keep the game's level.

The engine function `main+0x5cc0a0` enables the graph/resource families for that
level and mode (`0x210..0x320`) before updating scene parameters. Independent
resource consumers at `0x5b1fb8/0x5b1ff4` and `0x5b6534/0x5b656c` index the
resource families at renderer `+0x90/+0x150` by mode and level. This is an engine
resource selection, not a change to a final scaling blit or shader uniforms alone.

For output W×H, level L corresponds to factor `1 - 0.1*L`, with widths derived
by integer subtraction and heights by the original float table and truncation.
Thus level 5 is 960×540 docked or 640×360 handheld, and level 0 is the full
native output. In particular, the engine has no 75% resource family.

The four additional selectors at renderer `+0xd98/+0xe40/+0xee8/+0xf90` are
independent from the principal level. Their computed sizes occupy stack
`+0x180..+0x19c` and feed separate consumers at `0x5cd1c8..0x5cd288`.
The patch leaves those selectors and their graph settings untouched. Principal
level-dependent intermediate families are handled by the original function,
including the repeated half-size chain at `0x5cce50..0x5cd150`.

Output parameters at stack `+0x1a8/+0x1ac`, display mode selection and the native
photo readback path are unchanged by the helper. This describes the write scope;
it does not establish image quality, HUD alignment or photographic evaluation
correctness without game acceptance tests.

## Evidence and acceptance

`tests/test_snap_render.py` compiles the actual C helper into a native fixture.
It checks all six levels in both modes, strict default behavior, whole-renderer
canaries, unchanged CPU state, rejected unsupported options, read-only/short/
invalid memory and bounded diagnostic output. No proprietary input is needed.

`NEWSNAP_RENDER_TRACE=1` emits at most 64 changed configurations: old/new level,
native mode, expected engine scene dimensions and output dimensions. These are
configuration diagnostics, not measurements of allocated or rendered GPU targets.

Before claiming game verification, use identical title/tutorial/gameplay and photo
workloads with `game`, 50 and 100, then intermediate levels. Check actual NVN/Vulkan
color/depth dimensions, clear/viewport extent, unchanged output/HUD/encuadre,
photo capture and evaluation, album transitions and save persistence. Compare GPU
time and memory with equivalent shader-cache state, confirm no new skipped copies,
validation errors, shader failures or missing passes. Keep timing and photographic
correctness independent of FPS presentation settings. Arbitrary output sizes,
supersampling and temporal upscalers require separate resource and camera work.

### Initial GPU acceptance (2026-11-13)

Isolated 12-second probes, physical input disabled, RTX 4060, same copied initial
save, docked, 640x360 host window and FIFO relaxed: levels 50 and 100 exited 0
with 621 and 613 presents respectively, zero unimplemented NVN calls, validation
errors, shader failures or skipped draws. Vulkan reported the requested
`fifo_relaxed` mode on this driver. GPU pass telemetry records active 960x540
intermediates and a 480x270 depth pass at 50; at 100 it records larger 1920x1080
intermediates and 960x540 depth. Output remains 1920x1080 in both.

These probes reached the introductory 3D camp scene. Their final screenshots are
at different transition phases; they are not an image-equivalence or performance
comparison. Intermediate levels, handheld output, later gameplay and photo
capture/evaluation/save still require acceptance testing. No speedup is claimed.
