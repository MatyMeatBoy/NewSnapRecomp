# Lossless storage for generated HD shadows

The generated mod already uses BC6H lighting and BC3 shadow masks with mipmaps.
Dropping mips, shrinking maps or changing block formats would change its output.
The optional `newsnap.shadow_storage.enable_generated_compression(folder)` instead
sets ordinary NTFS compression on the generated output directory before new
`.part` files are written. Rename to `.dds` retains the attribute. File bytes,
hashes, DDS decoding and the runtime loader are unchanged.

The helper does not recursively compress existing files. It rejects symbolic
links, junctions and other reparse points in the directory path. Non-Windows
systems and unsupported filesystems retain normal storage without blocking
generation. The caller supplies only its generated mod directory.

## Measured evidence, 2026-11-20

Six private DDS outputs from the bounded `hd-size-sample` generation were copied
into a new compressed directory under `build/next-release-20261120/`; source
files were read only. No game-derived file is committed or distributed.
All six copies matched the original bytes and SHA256 hashes. Windows
`GetCompressedFileSizeW` reported:

| File | Logical bytes | Compressed storage bytes |
|---|---:|---:|
| 04a4fefd539c34c5.dds | 87,524 | 24,576 |
| 6090639f594e693b.dds | 21,988 | 21,988 |
| 664253060d5f0d9b.dds | 1,398,244 | 176,128 |
| 8bbfa0ee64362f0d.dds | 87,524 | 73,728 |
| 9ffee7f276ef5bb8.dds | 349,668 | 45,056 |
| e631cc5796520422.dds | 21,988 | 21,988 |
| **Total** | **1,966,936** | **363,464** |

This sample saves 1,603,472 bytes (81.5%). It is a small, nonrepresentative sample;
**it does not establish a whole-mod size or reduction ratio**. The ~6 GB startup
estimate should remain conservative until a full generation is measured.
An earlier fully synthetic BC3 fixture also confirmed inherited compression
through `.part` rename and identical bytes; its ratio is not a game-mod estimate.
NTFS can defer compression after closing a new file: immediate storage queries
may temporarily report the logical size. Measure after filesystem work settles.

## Tests and limits

`python -m unittest tests.test_shadow_storage` covers non-Windows no-op,
unsupported-filesystem fallback with existing bytes retained, directory-only
configuration, reparse-parent rejection before directory creation, and a native
Windows new-file inheritance/rename/byte-identity fixture.

Transparent decompression adds CPU work at file reads and compression adds work
while generating. No GPU, gameplay pacing, loading-time or full-mod benchmark
was performed for this storage change. Directory compression does not reduce
GPU memory or logical DDS size. Existing generated packs remain untouched.

Microsoft documents the directory inheritance and filesystem support contract:
[Creating and Opening Files](https://learn.microsoft.com/en-us/windows/win32/fileio/creating-and-opening-files),
[FSCTL_SET_COMPRESSION](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_compression).
This uses the Windows filesystem layer; emulator or renderer texture changes
are unnecessary because the DDS byte stream is preserved.
