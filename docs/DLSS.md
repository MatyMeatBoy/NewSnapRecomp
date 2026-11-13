# Optional NVIDIA DLSS Super Resolution

The native 0.4 integration can use NVIDIA DLSS Super Resolution, including DLAA
at native resolution. This is a temporal scene upscaler, not frame generation or
ray reconstruction. [NVIDIA advertises Super Resolution for all GeForce RTX GPUs](https://www.nvidia.com/en-us/geforce/news/dlss-4-5-super-resolution-available-now/);
actual availability is decided by the installed driver's NGX capability query.
An RTX GPU, current compatible NVIDIA driver, valid scene depth/motion/jitter,
and the model DLL are all required. Provisioning the DLL alone does not establish
that a scene is rendered correctly.

## Reproducible dependency

The optional runtime comes directly from the official [NVIDIA DLSS repository](https://github.com/NVIDIA/DLSS),
[stable SDK v310.9.16](https://github.com/NVIDIA/DLSS/releases/tag/v310.9.16),
released October 16, 2026. The immutable source commit is
`9981c6350dc58c0ce21f024fd65e31e851c31689`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `lib/Windows_x86_64/rel/nvngx_dlss.dll` | 58956912 | `d00b5b0ab29c3ca101b70c3a5ecb3a01b7ef33766a3383a28a18623083e6123e` |
| `LICENSE.txt` | 26620 | `d4216e39ebef5f9b50a6712ebb37beeb5379862a67733a9999c651f21592aaf0` |

The actual Windows release DLL reports file/product version **310.9.16.0**.
On the development machine, `Get-AuthenticodeSignature` reported `Valid`, signed
by NVIDIA Corporation. These observations describe the pinned DLL, not an
arbitrary driver override or future downloaded model. NGX can apply NVIDIA
driver/application overrides and model updates; the provision receipt identifies
the file supplied by this project.

Fetch and verify the optional cache:

```powershell
python tools/fetch_dlss.py
python tools/fetch_dlss.py --verify
```

Explicitly provision a native runtime folder (replace the example with the folder
containing the 0.4 native executable):

```powershell
python tools/fetch_dlss.py --install D:\path\to\native-runtime
```

For a previously verified cache without network access:

```powershell
python tools/fetch_dlss.py --verify --install D:\path\to\native-runtime
```

`--out` selects another cache. The Python interface is
`fetch(root=DEFAULT_OUT)`, `verify(root)` and `install(root, runtime_dir)`.
Installation checks the entire pinned dependency before writing the destination.
It copies `nvngx_dlss.dll` beside the executable and preserves the complete
unmodified license as `licenses/NVIDIA-DLSS.txt`, plus its version/hash receipt.
The cache stays under ignored `toolchain/`; no game content or keys are read or
uploaded. Released 0.3 packages are not changed.

The runtime loads the driver's `_nvngx.dll` from the NVIDIA Vulkan driver
directory (with the NGX registry path as fallback). That core belongs to the
installed driver and must not be copied from an unrelated SDK or driver.
Only the release SR DLL is fetched: no development/watermarked library,
`nvngx_dlssg.dll`, `nvngx_dlssd.dll`, Streamline middleware, or vendor headers
are required by this project's existing independently declared NGX ABI.

## Scene contract and presets

The [pinned SDK definitions](https://github.com/NVIDIA/DLSS/blob/9981c6350dc58c0ce21f024fd65e31e851c31689/include/nvsdk_ngx_defs.h)
define K = 11 for DLAA/Quality/Balanced, M = 13 for Performance, and L = 12
for Ultra Performance. These match the donor integration's existing per-mode
hints. A quality setting selects both render resolution and a model hint;
the NVIDIA driver still decides actual feature support.

The [Vulkan helper contract](https://github.com/NVIDIA/DLSS/blob/9981c6350dc58c0ce21f024fd65e31e851c31689/include/nvsdk_ngx_helpers_vk.h)
uses render-pixel jitter and motion vectors scaled to pixel space. For Snap's
render-resolution motion vectors and reversed device depth, creation flags must
include `MVLowRes` (`1 << 1`) and `DepthInverted` (`1 << 3`). `IsHDR` (`1 << 0`)
and `AutoExposure` (`1 << 6`) apply when supplying the linear HDR scene without
an exposure texture. There is **no DLSS depth-infinite creation flag** in this
SDK; do not borrow FSR's flag values. Motion vectors should exclude camera
jitter unless `MVJittered` is explicitly declared. The 0.01 near plane and
infinite far projection require correct scene reconstruction, not replacing raw
depth with linear depth before handing it to DLSS.

## Vendor terms

The DLL is proprietary software governed by the complete
[NVIDIA RTX SDKs license at the pinned commit](https://github.com/NVIDIA/DLSS/blob/9981c6350dc58c0ce21f024fd65e31e851c31689/LICENSE.txt).
It is not covered by this repository's MIT license. Keep the vendor terms and
notices with any optional binary distribution; do not describe the vendor DLL
as open source or distribute it as a standalone SDK product.

The license contains additional distribution obligations, including protective
end-user terms (section 2), SDK attribution/NVIDIA Marks in applicable
splash/about/credits surfaces (supplement 7.1(b)), and notification before a
commercial release (supplement 4). Retaining the license file is one part of
compliance; it does not fulfill every release obligation. No release notification,
trademark submission, game-content upload, or third-party contact is performed
by the provisioning tool. Review the complete pinned license when preparing a
public binary release.

## Verification

```powershell
python -m unittest tests.test_dlss -v
python tools/fetch_dlss.py --verify
(Get-Item toolchain/dlss-sdk-310.9.16/lib/Windows_x86_64/rel/nvngx_dlss.dll).VersionInfo
Get-AuthenticodeSignature toolchain/dlss-sdk-310.9.16/lib/Windows_x86_64/rel/nvngx_dlss.dll
```

The provisioning tests exercise integrity rejection, offline reuse, and license
preservation. Scene quality, temporal stability, and supported hardware require
separate native GPU validation.
