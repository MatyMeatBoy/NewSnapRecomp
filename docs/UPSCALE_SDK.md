# Official Vulkan FSR SDK integration

The optional AMD provider uses SDK **2.4.0**, pinned to official repository commit
`7539ae8b6568ad29ed78a753404351daf3b5cca7`. It includes FSR Upscaling 4.1.2 and
the analytical FSR 3.1.6 provider. The donor's separate 3.1.4 shader implementation
assumes ordinary depth and is not used for Snap's reversed infinite depth.

Run `python tools/fetch_upscaler_sdk.py` to fetch eight official files, or add
`--verify` for an offline integrity check. Every file has a fixed size and SHA256.
Downloads are bounded and replace a cached file only after verification. SDK files
remain under ignored `toolchain/fsr-sdk-2.4.0`; no binary is committed.
Build with `NEWSNAP_FSR_SDK` set to that absolute directory. `stage_sdk()` verifies
the files again and places the signed binaries and their license/third party
notices under the executable's `upscalers` directory. Source builds without this
option compile a portable unavailable-provider stub.

The API headers carry AMD's MIT notice. The signed binaries have the redistribution
license in `Kits/FidelityFX/docs/license.md`; they must not be described as MIT
source or reverse engineered. Both downloaded DLLs were checked with Windows
`Get-AuthenticodeSignature` and returned `Valid`, signed by Advanced Micro Devices.
The fetcher pins file contents; it does not depend on a machine's certificate store.

The bridge loads `amd_fidelityfx_upscaler_vk.dll` directly by an absolute Unicode
path derived from the executable, with `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR |
LOAD_LIBRARY_SEARCH_SYSTEM32`. It never searches the working directory or PATH.
The optional AMD loader is preserved in the package but is not needed by this
bridge. Export resolution failure leaves the normal rendering path available.

## Providers and device features

Provider IDs and names come from `ffxQuery` with the application's **existing**
Vulkan device. An explicit version override pins a context to the requested
queried provider. FSR3 therefore cannot silently select an FSR4 model. An FSR4
label is permitted only if a `4.` provider is returned and its enabled device
feature contract is satisfied. Model selection within that provider belongs to
AMD; there is no invented INT8 override or copied driver binary.
Auto prefers available DLSS, then an available FSR4 provider, then FSR3.

The donor already queries and enables supported Vulkan 1.1/1.2/1.3 core features.
The adaptation also queries and enables advertised `VK_KHR_compute_shader_derivatives`,
`VK_KHR_cooperative_matrix`, and `VK_EXT_shader_float8` feature structures when
available. This follows the pinned SDK's Cauldron Vulkan device setup. The FSR4
INT8 gate requires enabled derivativeGroupLinear. The SDK sample explicitly identifies
DerivativeGroupLinearKHR as required by the FSR4 INT8 prepass; additional model
requirements are left to the official provider query and context creation. All
supported core features remain enabled, including available FP16/INT8/storage/dot
features. The sample does not define those bits as a mandatory conjunction for
every FSR4 hardware model. Unsupported
extensions are never enabled by name alone.

AMD documents full INT8 model selection for RX6000/RX7000 and FSR4 Vulkan support.
This establishes an integration target for RX6900XT, not a test result on that
card. GPUOpen's overview and getting-started pages currently disagree about a
specific minimum AMD driver; provider and feature detection are authoritative
for this executable, and target-device validation remains necessary.

## Resource and lifecycle contract

`snap_fsr_sdk.h` exposes explicit descriptors for color, depth, motion, optional
exposure/reactive/transparency, and output. Validation rejects wrong dimensions,
MSAA, arrays, extra mip levels, stale generations, aliasing output, unsupported
formats, invalid camera/time values, absent exposure policy, and unverified scene
or device contracts. Motion vectors are current-to-previous displacement in render
pixels with no jitter; jitter is in pixels. The caller owns every image.

The Snap adapter uses the verified scene camera, HDR scene color, D32F depth and
portable camera/object motion reconstruction. It rejects unknown projection and
subresource layouts. Input images transition from GENERAL to
SHADER_READ_ONLY_OPTIMAL before SDK dispatch and return to GENERAL afterward.
The asynchronous Vulkan recorder is drained before direct SDK recording, and its
cached bindings are invalidated afterward. Output remains storage in GENERAL.
Contexts enable reversed/infinite depth and reset history on their first frame,
scene cuts, frame gaps and context/size changes. SDK return errors preserve the
unresolved rendering path.

Contexts are reused by output image, HDR policy and provider. Old contexts enter
a bounded retirement list and are destroyed after the maximum of their last
recorded evaluation's explicit fence and the latest issued submission fence; an
exhausted list declines optional work. Shutdown destroys contexts before images
and the Vulkan device. There is no per-frame device-idle wait.
Retirements are polled unconditionally at present, including after FSR is switched
off on a GPU with no NGX module loaded.

After creating a context, the bridge queries
`FFX_API_QUERY_DESC_TYPE_UPSCALE_GPU_MEMORY_USAGE` and logs the provider's
`totalUsageInBytes` and `aliasableUsageInBytes` verbatim. An unsupported or failed
query is logged as unknown. These are SDK effect context bytes; they exclude
application scene inputs, motion-vector/output images, staging resources and
other contexts, and do not establish total VRAM residency or a peak budget.

## Verification

`python -m unittest tests.test_upscaler_sdk -v` checks corrupted download handling,
staging rejection, exact source seams, CPU-side descriptor failures, portable
fallback, and compilation against the real downloaded SDK headers.

`tools/upscaler_probe.c` is a standalone diagnostic compiled with the SDK bridge,
Vulkan headers/library and `NEWSNAP_FSR_SDK=1`. Put its executable beside the staged
`upscalers` directory. Its default mode queries providers only; `--dispatch` also
allocates a small constant-color HDR scene with reversed infinite depth and zero
motion, creates the first returned provider context, records dispatch, submits
the command buffer and waits for completion. It creates its own diagnostic device;
the game always queries and dispatches on its existing device.

On 2026-11-13, RTX4060 Laptop GPU returned:

| ID | Provider |
| --- | --- |
| `f5a5ca1e00c01006` | 3.1.6 |
| `f5a5ca1e00803004` | 2.3.4 |

The official 3.1.6 synthetic HDR/reversed-infinite-depth dispatch was submitted and
completed successfully. No FSR4 provider was offered on this NVIDIA GPU. This does
not verify Snap image quality, motion stability, performance, RX6900XT operation,
or VRAM residency. Those require gameplay captures and target-device measurement.

Primary references:

- [Pinned SDK release](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases/tag/v2.4.0)
- [AMD FSR SDK overview](https://gpuopen.com/amd-fsr-sdk/)
- [AMD FSR4 integration](https://gpuopen.com/manuals/fsr_sdk/techniques/super-resolution-ml/)
- [Pinned Vulkan device sample](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/blob/7539ae8b6568ad29ed78a753404351daf3b5cca7/Kits/Cauldron2/framework/render/vk/device_vk.cpp)
- [Pinned API contract](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/blob/7539ae8b6568ad29ed78a753404351daf3b5cca7/Kits/FidelityFX/api/include/ffx_api.h)
- [Pinned binary license](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/blob/7539ae8b6568ad29ed78a753404351daf3b5cca7/Kits/FidelityFX/docs/license.md)
