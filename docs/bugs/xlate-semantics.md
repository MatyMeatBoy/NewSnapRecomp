# XLATE-SEMANTICS-07: BFE/BFI and funnel shifts

The pinned translator could pass an out-of-word Maxwell bitfield directly to
SPIR-V, or shift a 32-bit intermediate by 32 during a zero-count funnel shift.
SPIR-V does not define those results. A driver lowering shifts modulo 32 can
produce `A | C` instead of the unshifted source word. This is a portable shader
translation defect, not a confirmed cause of the RX 6900 XT photo/device faults.

## Source and scope

The infrastructure remains pinned at Astral
`248e0b29f308ca84a2d2092019cc60e7fc50ae85`, using its public Ryujinx 1.3.2 vendor
and original twelve translator patches. [TotK commit
c0e66fe4c1d532e728444c3ade6ff390f734151b](https://github.com/valentderah/totk-pc-recomp/commit/c0e66fe4c1d532e728444c3ade6ff390f734151b)
(2026-11-03, confirmed in that project's main during the 2026-11-14 audit) provides
the BFE/BFI correction and zero-funnel precedent. Its AMD/RADV workload results
are upstream author evidence; our local verification below is CPU-only.

The new adapter stages `0013-bitfield-defined-ranges.patch` and
`0014-funnel-defined-shifts.patch`, and changes the staged builder to require the
exact fourteen reviewed filenames. Missing/unexpected patches fail instead of
silently changing the translator recipe. Our existing
`0012-motion-previous-position.patch` remains byte-identical. The donor checkout
and vendored Ryujinx tree are not edited.

BFE/BFI clamp width to the remaining bits of the 32-bit word. An unsigned field
starting beyond the word extracts zero; a signed nonempty field there repeats the
source sign bit. A zero-length field extracts zero. An insertion entirely beyond
the word preserves its destination. Bit reversal still precedes extraction.
Constant fields already within the defined range keep the existing fast path.
Offset 32/count 0 is legal under the [Khronos SPIR-V
specification](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html#OpBitFieldSExtract),
which excludes values greater than the word width rather than equal to it.

Funnel shifts select C for zero-count left and A for zero-count right. Both
branches' intermediate shift counts are masked into 0..31, including arithmetic
that is later discarded by a select. The effective original count still chooses
the existing 32/64-bit endpoints. No new saturation behavior is inferred from PTX;
the donor's nonmasked count-at/above-limit result stays unchanged. Existing
signed right behavior and requested condition-code updates are retained.

Blanket initialization of unwritten registers/function locals is deliberately
held for separate hardware/ISA provenance. This change does not alter that policy,
shader resource reflection, game logic, runtime async policy or vendor detection.

## Verification

The tests compile the **actual prepared C# method bodies** for EmitBfe, EmitBfi,
EmitShf and ClampBitfield into a public authored typed IR fixture, rather than
reimplementing the emitter in the test. A separate bit-by-bit oracle covers all
256x256 field geometries with constant/dynamic operands, signedness and reversal:
655,360 cases. A concatenated-word oracle covers 262,080 funnel cases (including high unsigned counts and independent word patterns) across
32/64-bit modes, left/right, constant/dynamic counts, masking and condition codes.
The evaluator checks every emitted intermediate for undefined operand ranges,
including select arms. Old twelve-patch methods fail; fourteen-patch methods pass.

The fixture also compiles the full managed translator from the prepared sources.
Nine publicly authored Maxwell compute snippets exercise BFE/BFI and SHF, each in
optimized/debug mode: all eighteen translate successfully. The generated SPIR-V
passes Khronos `spvValidateBinary` in Vulkan 1.2 mode. Dynamic operations remain in
the output; immediate zero funnels fold to no shifts. Validation alone does not
prove dynamic arithmetic semantics: the actual-method oracle supplies that check.
No proprietary shader inputs are used.

Reproduce the focused tests with .NET 10 on the process PATH or
`NEWSNAP_DOTNET=<absolute dotnet executable>`:

```text
python -m unittest discover -s tests -p test_xlate_semantics.py -v
```

The full translator integration test accepts `NEWSNAP_XLATE_EXE=<fresh NativeAOT ac_xlate.exe>`
or `NEWSNAP_XLATE_DLL=<fresh managed ac_xlate.dll>` with .NET, and
`NEWSNAP_SPIRV_VALIDATOR=<spirv-val executable>`; it invokes the validator with
`--target-env vulkan1.2`. Without these optional tools that integration test skips
explicitly. `NEWSNAP_XLATE_PROOF_DIR` places generated projects/results in an
isolated build directory. No GPU is required.

The 2026-11-14 local run passed all six tests. The full managed build reported zero
warnings/errors. The real NativeAOT output also passed all eighteen synthetic
translations and Vulkan 1.2 validations. The local validator used the official Khronos glslang 16.6.0
Windows release static SPIRV-Tools library with a tiny C API driver; release asset
size/digest matched GitHub metadata. Its official `known_good.json` pins
SPIRV-Tools `ef96ed763b43b59b33b31b362f09a02b729fa1c9`; the driver uses that pinned
public `libspirv.h`. Acquisition receipts, generated binaries and validation
results remain private build artifacts, not source dependencies.

## Delivery and remaining checks

The translator identity hashes its build script, Program.cs, project file,
patches and vendor inputs. Build a real NativeAOT executable and matching `.id`;
changing only an identity beside an old executable is invalid. Build/package paths
must select that verified tool instead of copying the previous SDK executable.
The checked-in `profiles/translator-windows.json` pins the actual NativeAOT
SHA-256, size and recipe identity. `newsnap.translator` checks both binary and id
before owner verification/generation, before and after staged copying, and at
public-kit source/destination gates. A forged current id cannot bless an old SDK
executable. Corruption during a staged copy fails before replacing previous tools.
The current development build intentionally rejects the unmodified donor SDK and
the older published 0.6 kit; a matching public fourteen-patch kit is not published
yet. Maintainers use a separate verified staging SDK without modifying the old
SDK/release. Preserve
observed original shader inputs while re-keying compiled caches using the new
identity.

For a maintainer who already has the approved native build output, install its
pair into a **separate SDK staging directory**, keeping the old SDK intact:

```powershell
.venv\Scripts\python -c "from newsnap.translator import stage_translator; stage_translator(r'path\approved-translator-output', r'path\verified-sdk\bin')"
```

This checks the source and copied bytes against the committed public pin. It
rejects an old executable even if somebody changes its identity file. A local
NativeAOT rebuild can differ in binary hash with toolchain/build inputs; do not
change the pin or use `--id-only` to bypass the check. Reproduce and review that
build before approving a new pin. Until a matching kit is published, the old
public 0.6 kit remains usable only with its own immutable source recipe.

AMD hardware acceptance and an exact-gameplay comparison remain outstanding.
There is no FPS improvement claim or claim that this repairs existing saved photos.

## Third-party notice

The BFE/BFI patch derives from the TotK commit linked above; the funnel correction
uses its zero-count rule and additionally totalizes intermediate shifts. Preserve
this notice in distributed source/tool notices:

MIT License

Copyright (c) 2026 Valiantsin Dzerakh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
