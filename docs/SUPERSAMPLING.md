# Snap supersampling: implementation contract

## 0.2 implementation update

The shipped direction is native engine resizing, restricted to TV mode. The
host-scaling proposal below remains research. Initial GPU probes reached
2400×1350, 2880×1620 and 3840×2160 scene/depth passes. Visual review then found
that the original fixed output texture and native caller fields cropped the
result. Forcing the window resource resize flag was tested and crashed: that resource
lacks a reconstructible engine config, so the write was withdrawn. The accepted
candidate preserves that flag, updates caller dimensions with guest ORR/MOV, and
uses a strictly classified DISPLAY-only host backing image. The engine supplies
already-scaled raster coordinates, while CPU readback retains logical dimensions.
A 25-second 2× probe exited 0 (1,317 presents, no unsupported NVN calls, validation
errors, shader failures or skipped draws). Reviewed images show an entire centered
logo and intact character/vegetation/bird geometry. They are at different cinematic
phases, not an image-equivalence proof. Photo scoring/persistence remains unverified.

Handheld supersampling is withheld: its resources remained native and images
showed misaligned geometry despite zero API validation errors. Native 50–100 %
handheld remains available. Image correctness and photographic evaluation are
separate from target-size evidence.

Research for 0.2 alpha, 2026-11-13. This document is a design and evidence
record, not a claim that 125/150/200% have passed game or photographic tests.
This pass changed documentation only and ran no game/GPU work.

## What the reference projects actually do

| Project | Mechanism | Relevant constraint |
| --- | --- | --- |
| Pinned Astral 1.14, `248e0b29f308ca84a2d2092019cc60e7fc50ae85` | Its `res` patch changes engine size sites, dynamic-level comparisons and render-target budget. Larger output targets are rendered by the game, then reduced for the host window. | Its measured budget model and instruction addresses belong to Astral. The current host `scale` path primarily enlarges recognized shadow maps. |
| TotK upstream, inspected 2026-11-13 | Separate engine output and scene patch sets; larger scene supports supersampling. It grows DynamicTextureAllocatorMem, Graphics and the application pool. | The engine final pass resolves scene into output; without the verified heap table the patches stay off. Neither its BYML heap names nor its engine sites establish a Snap allocation contract. |
| Witch Time upstream, inspected 2026-11-13 | Host image scaling with a screen-resource class, coordinate conversion, upload/readback/copy paths and shader translation support. | Storage-written images and dependent depth-pyramid resources need explicit native-size exceptions; scaling dimensions alone caused lighting/culling artifacts. |

Primary sources: [Astral resolution implementation](https://github.com/captainj-sparrow/astral-chain-pc-recomp/blob/248e0b29f308ca84a2d2092019cc60e7fc50ae85/runtime/resolution.c),
[TotK resolution implementation](https://github.com/valentderah/totk-pc-recomp/blob/main/runtime/resolution.c),
[Witch Time renderer](https://github.com/Zexyen/Witch-Time/blob/main/runtime/nvn_vk_draw.c),
[Witch Time depth-pyramid rule](https://github.com/Zexyen/Witch-Time/blob/main/runtime/rs_pyramid.h),
[Witch Time validation history](https://github.com/Zexyen/Witch-Time/blob/main/docs/STATUS.md).
Upstream `main` links describe the versions inspected on this date, not a local
dependency upgrade. No source from those repositories was copied into runtime.

## Existing Snap boundary

Main build ID `ddb900ff04a912ed42430508389853cfaf1accce`, original NSO SHA256
`ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443`:

- `main+0x5cc0b0`, original word `b94ce808`, reads renderer `+0xce8` before the
  native graph selection. This field accepts only levels 0..5 (100..50%).
  It is an index into actual resource families, not an unrestricted percentage.
- Resource consumers at `0x5b1fb8/0x5b1ff4` and `0x5b6534/0x5b656c` index
  families at renderer `+0x90/+0x150` by mode and level. Passing a negative
  level for 125/150/200 would index outside these arrays.
- `0x5cc0a0` enables level/mode graph families at `+0x210..+0x320` and updates
  associated shader parameters. Its stack `+0x1a0/+0x1a4` holds nominal scene
  dimensions; `+0x1a8/+0x1ac` holds native output dimensions.
- Four other selectors at renderer `+0xd98/+0xe40/+0xee8/+0xf90` supply
  independent sizes at stack `+0x180..+0x19c`, consumed by `0x5cd1c8..0x5cd288`.
  They are not substitutes for the principal scene selector.
- Intermediate chains at `0x5ccd0c..0x5cd1c8` derive several resource/parameter
  sizes from the selected native family, including repeated halving. Overwriting
  only the nominal scene pair changes parameters without creating larger images.

The old `build/research/gpu-dump` is not a validated gameplay manifest: its frame
200 outputs are uniformly zero. It reveals a 960×540 / 1920×1080 / half-size chain
but cannot identify the complete visible 3D/photo resource closure.

The existing `build/updated/shader-cache` metadata snapshot contains 3,515
reflection files (1,865 fragment, 1,646 vertex, four compute), 10,495 texture
bindings and two image bindings. Both image bindings are compute-stage 2D stores
with flags 7 (`ResScaleUnsupported | NeedsScaleValue | ImageStore`), and an unknown
declared image format. Twenty-five texture bindings require scale values. These
are cached metadata counts, not unique live resources or proof that those stores
touch the scene. They establish that storage exclusions and scale-aware shader
reads must be checked against Snap's actual bindings rather than assumed absent.

## Recommended implementation

Preserve the existing native path for `game` and 50..100. For supersampling,
select native level 0 and treat `S=1.25/1.5/2` as a separate host scene-image
scale. Never encode those percentages into `+0xce8`. The targeted host approach
avoids inventing guest heap sizes, but requires the resource contract below.
An eventual engine allocation patch is also valid; it must identify Snap's
resource constructors, allocation budget and all size consumers first, as Astral
does. Those sites have not yet been established here.

The host implementation should retain original NVN descriptors and guest storage
layout. Each recognized image gets a separate allocation with physical dimensions
`round(W*S) × round(H*S)` and logical dimensions W×H. Store actual physical/logical
ratios, rather than assuming rounding always yields exactly S. Output, UI, photo
analysis, native tiling grids and other excluded resources remain scale 1.
At 1080p, the nominal full scene sizes are 2400×1350, 2880×1620 and 3840×2160;
at 720p, 1600×900, 1920×1080 and 2560×1440. 200% means twice each side and
approximately four times the pixel work/storage for the scaled resources.

### Identify and close the scene class before enabling it

Use the verified renderer identity and selected family as the seed. Correlate
engine resource objects with the resulting NVN texture identity/generation and
shader bindings. This association still needs implementation/evidence; the
family offsets do not by themselves identify an `NVNtexture *`.

Record creation, aliases, all attachments in a pass, sampled/storage bindings,
copy edges, first output/HUD composition and every CPU/photo consumer across
title, tutorial, gameplay, photo capture and album transitions. A width/height
match or 16:9 aspect alone is insufficient. The four independent engine selectors
must be classified by their observed consumers, not multiplied indiscriminately.

All color/depth attachments of a scaled pass must agree on their physical scale.
Follow screen-space color/depth and blur/bloom dependencies only when their
sampling semantics support it. Keep LUTs, shadows, materials, CPU uploads,
resource aliases with incompatible semantics, storage-written images and native
tile/culling/depth-pyramid chains at their verified size. A scaled-to-native color
composition is the boundary at which supersampled scene resolves before native
HUD and photo analysis. If no such boundary is established, scene-only scaling
must remain unavailable; scaling the final frame is a distinct scope.

### Required host contracts

| Area | Change / guard required before claiming support |
| --- | --- |
| Allocation/cache | Scale only identified scene textures, use owned memory, account actual VMA bytes, and include class/scale/generation in image/view/descriptor cache identity. Never bind a larger image into original guest pool storage. Check device format/extent/sample limits and total budget before committing the class. |
| Viewport/scissor/clear | Use the physical/logical ratios for every region, including nonzero origins and partial clears. Existing `pass_scale` supports enlarged passes but chooses the maximum of attachment scales; mixed attachments need rejection or an explicit resolve, not silent cropping. |
| UBOs | Keep game camera matrices, logical dimensions and original UBO snapshots unchanged for the host-scaled path. Update host support-buffer values, not arbitrary guest constant offsets. Engine-resized resources would require a different UBO/size contract; do not mix the two approaches. |
| Fragment coordinates | `gl_FragCoord` must present logical game pixels to game shaders while rasterization covers the enlarged target. Current `support_scales` is gated on `AC_TEX_MIP_SKIP`; enable its population independently for supersampling. |
| Integer fetch/size query | Populate per-binding scale metadata for fragment, vertex and compute consumers where the translator supports it. `GfxShaderRes.flags` exposes `ResScaleUnsupported=1`, `NeedsScaleValue=2`, `ImageStore=4`, `ImageCoherent=8`. Reject unsupported uses or keep the complete affected dependency native. Bindless/indexed/array and storage-write cases need explicit treatment; metadata `scale_idx` alone does not prove safety. |
| Image transfers | Translate each endpoint's logical region into its own physical region. A partial interval should use rounded endpoints, `round((x+w)*k)-round(x*k)`, to avoid inconsistent extents. Distinct scales require supported color blits. Depth/stencil and multisample conversions require an actual valid path; do not silently omit them. |
| Buffer transfers | Guest row/image strides and bounds remain logical. Image-to-buffer must resolve into a native-size compatible staging image before copying original guest bytes. Buffer-to-image must upload native staging then expand as appropriate. Barriers, fences, lifetime and error propagation must cover both operations. |
| CPU ReadTexels/writeback | Audit both direct ReadTexels and automatic `write_back`, including mip/layer/partial-row layout. Current `image_texels` samples the nearest enlarged texel for CPU reads; preserving dimensions alone does not establish photographic equivalence or a suitable antialiasing resolve filter. |
| Material LOD | Normalized coordinates naturally address the enlarged scene textures. Decide explicitly whether changed material LOD from higher raster density is intended; do not apply the temporal-upscaler negative bias blindly. |
| Native effects | Storage/tile masks can encode semantic pixels; normalizing fetch positions is not sufficient. Preserve their entire native dependency chain or add a measured specific conversion. Witch Time's depth-pyramid exception demonstrates this failure mechanism. |
| Downsample | Resolve scene once at the native composition boundary with a defined color-space/filter contract. For 2×, use an area-equivalent 2×2 reduction where valid; the current nearest CPU readback is not that filter. Preserve alpha and sRGB/linear format semantics. |

Relevant pinned source locations: `vk_texture.c` creation near 687, owned/pool
allocation near 766, `image_texels` near 2180 and `write_back` near 2301;
`vk_exec.c` attachment resolution near 383 and clear/scissor handling near 700;
`vk_exec_draw.c` support data near 1554/1624; `vk_exec_xfer.c` subresource region
conversion near 332 and buffer transfer near 417. The existing scaled
image↔buffer rejection is an independent blocker being addressed separately.
Ryujinx `ResourceManager.cs` marks unsupported scaling cases; `TexturePass.cs`
excludes bindless/indexed cases. Honor those signals in the host policy.

### Failure and lifecycle policy

Initially require restart when selecting supersampling. Before guest rendering
starts, verify the complete declared class, formats, limits, transfer support and
memory budget. If preparation fails, retain the complete native path and report
the requested and effective scale. Do not downgrade one attachment independently
after other members are already enlarged. Unknown resource/consumer discoveries
must produce bounded diagnostic evidence and prevent promotion of the feature;
late demotion requires synchronized content-preserving recreation of the whole
affected class and is outside the initial implementation.

Resource identity must include generation to survive transitions/address reuse.
Cache eviction/recreation must preserve classification. GPU completion must
precede freeing converted images/views/staging resources. Budget each class with
its observed format, mips, layers, samples and in-flight copies; the useful rough
increment is `(S*S-1)*native_class_bytes`, but actual VMA allocations determine the
limit. Astral's 110 bytes/pixel fit is not a Snap memory budget.

## Acceptance before a 0.1.2 alpha claim

Offline: exact-build/opcode checks; synthetic 1.25/1.5/2 image classification,
rounding and cache identities; mixed-scale/MRT/depth rejection; every transfer
direction with partial crops, padded rows, multiple layers/mips and guard bytes;
sRGB/UNORM/float format filters; unchanged native output/photo buffer sizes;
shader-scale metadata tests with mip skip both off and on; allocation failure
before enabling the class; safe lifetime after queued transfers.

GPU, separately authorized and measured by the implementer: repeat identical
100/125/150/200 routes. Confirm actual scene color/depth dimensions and native
HUD/output dimensions, visibility, water/particles/effects, menu blur, transitions,
photo/album/save behavior and unchanged photographic evaluation inputs. Require
no new omitted transfers, shader failures, validation errors or incomplete passes.
Measure frame distributions and peak VRAM, and capture matched images after shader
warmup. Establish both correctness and a real high-resolution raster; a saved
preference, enlarged swapchain or final sharpened upscale proves neither.

Status: the references support a targeted host adaptation as an engineering
approach, while the resource closure, composition boundary and full transfer/
shader contracts above remain prerequisites for calling Snap supersampling safe.

## Engine resize investigation and opt-in prototype

The follow-up below investigates the engine route as an alternative to the host
scene class. It does not supersede the acceptance requirements or establish a
shipping feature. Only a controlled run can show whether the game's marked
resources cover its 3D image and whether the existing pools are large enough.

### Native resize path found

`main+0x98d160` receives x0=result storage, x1=graphics context, x2=width,
x3=height and w4=flags. It drains/synchronizes engine work before dispatching
the requested resize operations. The two direct callers found in main are
`0x5d6d54` and `0x634e6c`, both using the original flags value 2.

| Flag | Observed engine operation |
| --- | --- |
| 1 | `0x989080` updates width/height parameters of type-0xd draw objects whose `+0xd0` resize-enabled flag is set. |
| 2 | `0x98d160` updates output width/height at context `+0xa8` object `+0x38`, calls **nvnWindowSetCrop**, and may recreate its associated resource when context `+0xc8` object `+0x14` enables this. Changing crop is not proof of a larger window texture. |
| 4 | `0x989080` iterates its `+0x10/+0x18` resource-group vector, 0x28-byte entries, invoking `0x8e2aa0` for entries marked at `+0x20`. |

`0x8e2aa0` preserves resource descriptions, recreates the owning configuration
through closure `0x8e4850`, and restores categories of preserved descriptions.
At `0x8e4a30..0x8e4a3c` the closure writes its supplied width/height into the
new configuration at `+0x18/+0x1c`, then invokes the owner's virtual creation
method at `0x8e4a5c`. This is a promising real engine resource resize boundary.
It is not evidence that every scene group is marked resizable.

The central NVN texture creation path at `0x8f8510` reads description W/H at
`+0x18/+0x1c` (`0x8f8774/0x8f8780`) and invokes SetSize2D at `0x8f87ac` through
the resolved function pointer at `main+0x1489270`. It obtains the resulting
NVN GetStorageSize at `0x8f87bc`, aligns to 4 KiB, then requests pool storage.
This offers a direct measurement boundary: NVN descriptors themselves must grow
with an engine resize. No host image `scale` field is needed for that path.

### Allocation evidence and remaining budget question

The engine resolves nvnMemoryPoolBuilderSetStorage into `main+0x14890a0`.
The shared pool builder at `0x911c40` accepts requested bytes in x3, rounds to
2 MiB, obtains storage through `0x8dc340/0x8dacc0`, and supplies the rounded
allocation to NVN at `0x911cf8`. Additional pools at `0x90df94..0x90dfa4` come
from configuration entries, likewise rounded to 2 MiB. Texture creation searches
those pool allocators at `0x8f8840..0x8f88e4` using actual storage size and
alignment. These are allocator sites, not proof of a sufficient render budget.
No Snap equivalent of Astral's measured render-budget constant has been verified.
Do not patch its allocator page counts or all pool budgets using donor numbers.

The configuration near `0x90d790..0x90d810` copies separate shader, descriptor,
uncached and other pool budgets from its input configuration. Their labels and
sizes must be distinguished from target texture pools. An oversized output
request can exhaust an existing guest pool even if host VRAM remains available.

### Why changing only the width constants is insufficient

The two callers pack W/H into x20 or x19, then extract width using
`and x2,<packed>,#0x780` (`0x5d6d44`, word `92790e82`; `0x634e5c`, word
`92790e62`). This is a compiler optimization valid for the native 1280/1920
values. It is not a general 128-pixel alignment rule. With packed width 3840,
this mask yields 1792; with 2400 it yields 256. A generic replacement would
extract low 32 bits, not apply `~127`, which also incorrectly truncates 2400.

Function `0x5bcad0` maps exact authored docked dimensions to handheld dimensions,
including 1920→1280, 1080→720, 960→640 and 864→576. Its callers at
`0x5bc8cc/0x5bc8d8` and `0x5bd1a4/0x5bd1b0` build the two sets of six native
resource levels. Replacing output constants alone would not extend these exact
comparisons to arbitrary larger sizes.

### Implemented experiment, disabled by default

Files `newsnap/overlays/snap_supersample.c` and
`patches/snap-2.0.1-supersample.txt` provide a narrow experiment. The table
defaults `AC_SNAP_SUPERSAMPLE_PATCH` to 0. Enabling it with value 1 and choosing
`AC_RENDER_SCALE=125`, `150` or `200` changes only the two verified resize calls:

| Site | Verified original | Replacement sequence |
| --- | --- | --- |
| `main+0x5d6d54` | `940ed903`, BL `0x98d160` | `snap_supersample_resize(Cpu *)`, then original BL |
| `main+0x634e6c` | `940d60bd`, BL `0x98d160` | `snap_supersample_resize(Cpu *)`, then original BL |

The helper accepts only full 64-bit argument pairs 1920×1080 or 1280×720 and
flags exactly 2. It multiplies x2/x3 by the chosen exact percentage and sets
x4 to 7, requesting output, eligible draw-parameter and eligible resource-group
resize together. Flags 5 would omit the output operation and are inappropriate
for this output-supersampling experiment. Other registers, NZCV, memory and
arguments are untouched. `game`, all native scale options and unknown options
are strict no-ops. The original call is replayed after the helper, maintaining
its original guest call/return site. No guest function is recursively invoked
from the helper.

Because the helper runs after the native width extraction, this prototype does
not modify the risky AND instructions. The engine still supplies valid native
arguments before scaling. The integration must select native level 0 for >100
instead of passing an out-of-range index to the principal resource families.

**Known mismatch:** the callers still hold native packed x20/x19 and native
height x21/x23. Their subsequent output-field stores at `0x5d6d78` and
`0x634e90/0x634ec8` retain native values. Initial display writers at `0x5d4b24`,
`0x5d4fe0` and mode events at `0x5dc454` also remain native, as do the original
level-dependent parameter updates in `0x5cc0a0`. Some later update may therefore
restore native parameter values or size assumptions after the experimental
resize. This is intentional narrow test scope, not a resolved full-output patch.

No assumption is made that photographs resolve automatically to their original
dimensions. Engine-resized logical NVN resources differ from host-scaled images:
the existing host `scale` conversion may be 1 throughout. Photo capture buffers,
row sizes and evaluation sources must be observed after the engine resize,
and a native resolve boundary established if any of them change. The experiment
must not be presented as photo-compatible before that check.

`NEWSNAP_SUPERSAMPLE_TRACE=1` prints at most 32 accepted calls, recording native
and enlarged arguments, flags and the caller-field mismatch. These are argument
traces, not proof of enlarged NVN allocations. The test fixture compiles the
actual helper, checks all six mode/scale combinations, full CPU canaries,
native/invalid arguments, bounded tracing and helper-before-original-call
ordering. Both patch opcodes and their BL target were verified against the
exact extracted Snap NSO, and the helper passes syntax checking with real
runtime headers. No GPU or photographic result is claimed by those checks.

The next run must show increased W/H at `0x8f87ac`/NVN target creation and visible
rendering, with measured pool usage and no omitted/corrupt passes. If only output
viewport dimensions change or no resize-enabled scene groups exist, stop this
experiment and identify the missing engine registration or constructor contract;
do not substitute final presentation scaling as evidence of internal 2×.

## Follow-up evidence: docked growth, handheld failure

The parent implementer's controlled GPU matrix, recorded in
`build/research/ss-matrix.json`, reports actual docked depth targets of
2400×1350, 2880×1620 and 3840×2160 for 125/150/200, alongside native 960×540
auxiliary targets and 1024×1024 shadows. Those runs exited 0 with no reported
unimplemented NVN calls, validation errors, shader failures or skipped draws.
This establishes real target growth for those docked probes, not photographic
correctness or complete scene coverage.

In handheld probes the helper logged enlarged arguments, but pass measurements
remained 1280×720 and 640×360, with a 1920×1080 output. The parent also observed
black viewport borders and misaligned vegetation in `ss-handheld-125.png`.
Zero API/validation errors therefore did not establish rendering correctness.
Handheld supersampling must be rejected explicitly pending a verified fix;
native handheld scales remain a separate working path.

### Static cause identified for missing handheld resource growth

Resource registration function `main+0x9831d0` accepts x0=output handle,
x1=manager, w2=resource type, x3=configuration and w4=resize eligibility.
It stores `w4 & 1` into its manager `+0x10/+0x18` vector's 0x28-byte entry at
`+0x20`, the same flag read by resize function `0x989080`.
The adapter at `0x5cf000` forwards its first stack argument into w4 at
`0x5cf134/0x5cf150` before calling registration at `0x5cf15c`.

Constructor `0x5bc660` takes original resize eligibility in w6 and stores the
low bit in its local byte `[fp-0x68]` at `0x5bc698` (word `381983a8`).
It constructs six docked levels, followed by six handheld levels. After each
docked iteration, `0x5bc8ac` (word `381983bf`) clears this byte. Thus only the
first docked level can inherit original eligibility. By the handheld-loop
entry at `0x5bc8e8` (word `aa1f03f7`, initialize handheld level index x23=0),
the eligibility byte is already zero; subsequent handheld iterations also clear
it at `0x5bca5c`. Both families forward the same local-byte pointer to their
resource construction, so the handheld records are not marked eligible.

The second family constructor, `0x5bcf50`, takes original eligibility in **w4**
(not w6), stores its low bit at `0x5bcf88` (word `3819c3a8`), and follows the
same pattern with local byte `[fp-0x64]`: clear at `0x5bd184` (word `3819c3bf`) before handheld
level-index initialization at `0x5bd1c0`. This explains why enlarging the resize
request changes output/draw parameters while the active handheld scene resources
remain native. It also explains the docked level-0 target growth and unchanged
native auxiliary resource families. The observed visual failure is consistent
with that mismatch; a final causal game test is still necessary.

A prospective handheld fix should preserve the constructor's **original**
eligibility and restore it only for the first handheld level before its loop,
when the experimental handheld supersampling path is selected. It must not set
every manager entry's flag or enable levels/resources the original constructor
declared ineligible. A bounded per-call/frame record keyed by guest frame and
constructor could capture original w6 for `0x5bc660` or w4 for `0x5bcf50` and restore its bit at
`0x5bc8e8` / `0x5bd1c0`, without occupying unproven guest stack padding.
Records must distinguish nested calls, guest threads and both constructors;
native settings must perform no writes. This is a proposed next experiment,
not an implemented patch or authorization to remove the handheld guard.

Before promotion, test that eligibility changes only for originally eligible
handheld level 0, that native cases preserve byte-for-byte behavior, and that
actual handheld NVN dimensions grow to the requested size. Then repeat viewport,
effects, output/HUD and photo/album acceptance. Keep the explicit handheld
rejection until those observations succeed.

## Blocking docked visual finding and caller consistency

The parent subsequently compared matched logo shots at 100 and 200. The 200%
logo was enlarged and clipped toward the bottom/right, despite a 3840×2160
scene depth target and a 1920×1080 output image. Thus the previous docked target
growth is insufficient for a correct supersampling feature. Release of these
options must wait for an uncropped composition and photo checks.

The original post-call stores were verified again. At call `0x5d6d54`, x20 is
packed `W | (H << 32)` and x21 holds H. Both the normal store `0x5d6d78` and
the fallback `0x5d8744` use `stp w20,w21,[x8,#0x30]`; x20 is overwritten by
the next renderer pointer load at `0x5d8748`. At call `0x634e6c`, x19 is the
packed pair and x23 holds H. Stores `0x634e90` and `0x634ec8` use
`stp w19,w23,[x8,#0x30]`, after which x19 is restored from its saved stack
value at `0x634ea4/0x634ecc`.

A caller-specific helper can update the corresponding packed pair **and**
persistent height register together with x2/x3, after requiring that both still
match the original native arguments. Use separate verified wrappers for these
sites; do not infer the active caller from coincidental register contents.
Updating only the packed pair leaves the height store inconsistent. This can
repair post-call bookkeeping, but does not by itself establish resized output
texture allocation or supersampling correctness.

The indirect NVN function at `main+0x1489038` was resolved by its initialization
at `0x90a868..0x90a87c` and the original name at `0xb0702f`: it is
`nvnWindowSetCrop`. This clarifies why setting flags 7 can enlarge scene resources
while retaining a native output texture. The output resource recreation branch
at `0x98d2ec..0x98d34c` requires a nonzero byte at context `+0xc8` object
`+0x14`. The next diagnostic must inspect that eligibility and actual window
texture creation, rather than equating larger crop or metadata with output
allocation. `0x5d8770` also invokes the native parameter update `0x5cc0a0`
after the first caller, so later native size assumptions remain relevant.

## Next experimental correction: window eligibility and coupled stores

The current helper now validates the eight-byte resource pointer at graphics
context x1 `+0xc8` against readable guest memory, then validates the single byte
at resource `+0x14` against writable/readable guest memory and accepts only an
existing 0/1 value. For docked native 1920×1080, flags 2, and exact 125/150/200
settings, it sets that one byte to 1 before changing x2/x3/x4. This enables the
engine's existing window-resource reconstruction branch, rather than changing
only its crop. The flag remains enabled during the process so subsequent engine
output resizes can recreate the enlarged window resource. No other resource
group eligibility is modified. Invalid memory, an unexpected flag value,
handheld arguments, native choices and unknown choices leave CPU and RAM
unchanged. Pointer additions, region containment, permissions and integer wrap
are checked before any guest read/write. This is a narrowly guarded experiment;
the existing branch does not alone prove the new output allocation succeeds.

The patch now executes these original guest-register operations between the
common host helper and the original BL:

| Caller | Exact guest words / operations |
| --- | --- |
| `0x5d6d54` | `aa038054` ORR x20,x2,x3,LSL#32; `aa0303f5` MOV x21,x3; `940ed903` original BL |
| `0x634e6c` | `aa038053` ORR x19,x2,x3,LSL#32; `aa0303f7` MOV x23,x3; `940d60bd` original BL |

This makes the post-call STP fields agree with the requested engine size while
the host helper continues to preserve callee-saved registers. Native arguments
reconstruct exactly the native pair, preserving their original guest behavior.
The two ORR/MOV sequences were assembled using Keystone and decoded using
Capstone; both original BLs and the four post-call STP instruction words were
checked against the exact Snap NSO. The patch table is now enabled by default,
with the helper's native/handheld strict no-op guards; earlier disabled-default
descriptions above record the original prototype stage.

The expanded native fixture checks all supported TV percentages, unchanged
portable and native paths, a persistent already-enabled window flag, CPU-wide
canaries, byte-exact surrounding context/resource canaries, exact-end memory
spans, truncated/unmapped/read-only pointers, address wrap and nonboolean resource
flags. It verifies bounded tracing and patch guest-word/post-store semantics.
All three tests and real-runtime-header syntax checking pass. These remain CPU
and source checks: the next required observation is an enlarged output texture
and an uncropped matched image. Actual viewport/UI/photo acceptance and memory
sufficiency are still pending; do not publish the earlier cropped result as 2×
supersampling merely because its depth target grew.

## Window-rebuild crash and DISPLAY-only bridge experiment

The parent reports that forcing window-resource eligibility caused exit 71 at
`main+0x8f15d0`, through `0x8e3d74/0x98d350`, dereferencing null plus `0x1d8`.
That experiment failed. The single-byte eligibility change above must be
withdrawn; it is not a supported way to reconstruct Snap's output resource.

The next prototype combines engine-rendered larger scene resources with a host
allocation change **only for NVN DISPLAY textures**. This is a distinct, narrowly
classified bridge, not the general scene/material/depth scaling path discussed
earlier. It does not mark any extra engine resources eligible for resize.

`newsnap/output_adapt.py` supplies exact-once seams for staging; it does not edit
the donor checkout. `newsnap/overlays/snap_output_scale.h` supplies the actual
inline policy. The integration must merge `edits()` into source adaptation and
copy the header alongside the runtime. The engine helper returns to argument-only
behavior; guest ORR/MOV coupled-store corrections remain applicable.

Image creation in `vk_texture.c` accepts only descriptors carrying
`NVN_TEXTURE_FLAGS_DISPLAY=0x1`, optionally `COMPRESSIBLE=0x8`, and no other
flags. This excludes IMAGE/storage, video, linear, sparse and unknown usages.
Additional required fields are native 1920×1080, 2D, one mip, one sample,
depth/layer extent at most 1, and RGBA8/BGRA8 UNORM or sRGB. The resolved Vulkan
format must equal its ideal format, with no depth/stencil, expansion or ASTC
conversion. Only docked exact 125/150/200 choices increase dimensions, subject to
the device max-image-dimension check. The existing `scale > 1` allocation route
uses its own VMA allocation instead of binding a larger image into native pool
storage. Material, scene, depth, shadow, pyramid and non-DISPLAY textures do not
qualify on matching dimensions alone.

The physical display image and `VkTexImage.scale` take S, but the corresponding
render target's raster `scale` is forced to 1. The engine already emits enlarged
coordinates after its resize; applying S again to viewport/scissor would double
the enlargement. Other targets preserve their existing raster scale. Keeping
the image's scale allows the existing CPU ReadTexels/writeback logical-byte
conversion and lets presentation use its actual image extent. It does not
establish photographic equivalence: CPU reads currently choose nearest samples,
and NVN image-to-buffer copies still reject images with `pub.scale > 1` until a
proper native-size staging resolve exists. Reject release if those warnings occur
on the photo/capture route. Do not silently skip copies or alter guest row pitches.

The host present path multiplies the guest crop by image scale. For the known
full-window, zero-origin crop the overlarge extent is clamped to actual image
size; nonzero/partial crop behavior needs separate verification with this hybrid
coordinate contract. A larger screenshot alone does not prove correct final
composition. The next GPU acceptance must show the matched logo fully framed,
larger scene and display allocations, correct final downsample and native guest
photo dimensions, with no copy omissions or new validation/shader failures.

`tests/test_snap_output.py` compiles the actual inline policy using original NVN
descriptor definitions and the target-scale assignment extracted from the staged
`vk_exec.c` source. It checks classification, allowed/rejected flags and formats,
native and handheld strict behavior, exact supported factors, device limits and
unchanged ordinary/shadow scales. It also proves every source seam matches once
and that the donor's owned-allocation/pool guard remains present. Passing this
CPU fixture establishes source wiring and policy, not visual/GPU correctness.
