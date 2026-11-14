# PACE-CRC-01: portable IEEE CRC32 instruction specialization

Status: implementation ready for independent review; **not integrated or accepted
as a game performance improvement**. Published alpha and owner data are unchanged.

Fresh alpha CORE_DIAG long-wait owner captures identified the resource checksum
routine at main+0x15fe90. Its generated C uses the CRC32 ISA helper; the original
eight-byte helper performs eight serial table folds. These captures are selected
wait observations, not a CPU-time profile or proof that CRC explains every spike.
The earlier diagnosis ran on battery (ACLineStatus=0, 26%).

## Contract and implementation

`crc_isa_adapt.edits()` changes the IEEE CRC32 macro in staged `runtime/simd.h`.
Four/eight-byte instructions use slicing-by-eight, polynomial `0xedb88320`, with
least-significant byte first and a truncated 32-bit accumulator. Every argument
is evaluated once by an inline function. Widths 0, 1, 2, 3, 5, 6 and 7 still
call the original scalar helper; CRC32C and its `0x82f63b78` table are unchanged.
No shifts exceed 56 bits. No hardware CRC32C substitution or additional host CPU
feature requirement is introduced.

Seven derived rows have one `extern const` definition in `snap_crc_tables.c`:
7,168 additional immutable bytes. The original header's base row is reused.
`tools/generate_crc_tables.py --check` verifies deterministic regeneration without
game data. Tests check every entry against an independent bitwise polynomial
oracle, including the existing base row. There is no table initialization state.

The second adapter seam inserts `snap_crc32_init()` at the beginning of
`rt_patches_init()`, outside `RT_PATCH_COUNT`. This is a serialized startup call,
before guest execution; its once-only configuration read must not be called
concurrently. Missing/default configuration enables slicing; exact
`AC_SNAP_CRC32_SLICE8=0` selects scalar. Repeated startup calls retain the first
choice. The flag starts at BSS zero, so probes that do not call patches init keep
scalar behavior. No live setting or per-instruction configuration lookup exists.
The header supports C++ consumers through extern-C linkage.

This replaces an ISA operation implementation, without replacing the guest
function, VM loads, validation, scheduler checkpoints or any Cpu state update.
The RandomRange patches.c seam is inside its set loop and does not overlap these
include/function-entry anchors. The donor checkout remains unchanged.

## Verification, 2026-11-13

`python -m unittest tests.test_crc_isa`: **7 tests pass** using clang 23.1.4.
The first run failed because the new adapter did not exist. A private native
wrong-row mutation subsequently produced a different checksum and was detected;
the mutation exists only in disposable test output, never in the implementation.

- Actual adapted simd.h and actual adapted patches.c are compiled, including a
  no-patch-set initializer. Separate fresh processes verify scalar probe default,
  default-on, explicit opt-out and idempotent startup/config-read count.
- Known `123456789` vectors, every defined width 0..8, accumulator/input basis
  bits, all-one/zero and 1,000 random pairs match the independent bitwise oracle
  with both paths. CRC32C is checked independently too.
- Four simultaneous native readers each perform 1,500 checks against the oracle.
  The flag is selected before readers start; no concurrent mutation is tested or
  supported. Constant one/two-byte and CRC32C code has no startup-flag/table
  reference at O1. A C++ consumer links the C flag, table and initializer.
- Optional private test verifies original main SHA256
  `ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443`
  and build ID `ddb900ff04a912ed42430508389853cfaf1accce`, then uses the donor
  Emitter without patches to regenerate f_700015fe90. Separate translation units
  compile that function with donor scalar header and adapted header. All 1,024
  Cpu bytes match over 2,176 length/alignment cases (0..128 and boundary/large
  lengths, offsets0..15); the full 8,192-byte input remains unchanged. Extracted
  guest-derived code stays in ignored temporary build output, never committed.

## Bounded CPU micro measurement

Private reproducible harness and raw samples:
`build/v05-crc-isa/{measure.py,bench.c,measurement.json}`. Both paths fold the same
8 MiB through the actual helper/header, with equal resulting checksums. Six
measured iterations follow a discarded warmup; order reverses each iteration.
One thread, same process/compiler, no GPU or whole runtime build.

| Compiler optimization | Original median | Slicing median | Scalar opt-out median | Original / slicing |
|---|---:|---:|---:|---:|
| O1 | 15.057 ms | 3.426 ms | 15.050 ms | 4.39x |
| O2 | 14.999 ms | 3.530 ms | 15.007 ms | 4.25x |

GetSystemPowerStatus reported **ACLineStatus=1, battery25%** both immediately
before and after this brief measurement. This differs from the earlier battery
diagnosis; no cross-session timing comparison is made and no power-setting
change was requested or performed by the tooling. CPU reported AMD64 Family25
Model68; compiler target x86_64-w64-windows-gnu. Disassembled benchmark symbol
spans (including alignment padding) grew from112 to272 bytes at O1 and240 to368
at O2. These are harness loop footprints, not the whole game's code-size delta.

The helper measurement establishes reduced checksum cost only. Game frame tails,
resource/photo acceptance and physical AMD RX6900XT testing remain unmeasured.
No FPS claim follows from this test.

## Integration gates reserved to coordinator

Root must integrate `edits()` and copy/link all three overlay sources in normal
staging, obtain independent review, and inspect the compiled guest checksum
function for actual flag/table references. Header changes do not invalidate
generation-cache C outputs: emitted CRC32 calls remain identical. Native compiler
header/PCH dependencies must rebuild the affected objects; cached executables or
objects must never substitute for that rebuild. Probe startup should stay scalar,
normal startup should log the chosen path. Subsequent same-binary on/off A/B must
restore matching copied profile/cache/route and record power per run. Integration
was initially held while the coordinator diagnosed an unrelated launcher issue;
the 0.6 restoration below does not itself complete those integration gates.

## Restoration and CPU revalidation for 0.6, 2026-11-14

The seven files in `build/v05-crc-isa/held-source/inventory.json` were verified
against every recorded SHA256 before restoration. All destinations were absent;
restoration used exclusive file creation and independent copies, with destination
hash checks. The retained prototype and its historical measurements were not
overwritten.

Fresh revalidation with the project's `.venv/Scripts/python.exe` passes all seven
tests, including the private 2,176-case full-Cpu oracle, and the table generator's
`--check`. The default system Python lacks numpy for the optional private emitter
test; it is not the dependency-complete test environment. The old generator emits
an existing ResourceWarning about its NSO file handle; no donor code was changed.

The only implementation adjustment after restoring the prototype routes its
once-only startup message through `rt_log`, so it reaches the runtime's automatic
`newsnap.log` as well as stderr. A fresh-process regression first failed when the
prototype bypassed that logger; it now checks one config lookup and one runtime
log call despite repeated initialization. CRC arithmetic, tables, scalar opt-out
and guest-state behavior are unchanged. The original switch remains
`AC_SNAP_CRC32_SLICE8=0`; probes remain scalar until normal boot initializes it.

No selftest or TLR bounds are changed to make the candidate pass. Complete staged
integration, compiler dependencies and runtime acceptance belong to the
coordinator. The microbenchmark figures above remain historical CPU-only
measurements: no benchmark was rerun during the reserved GPU acceptance, and no
new FPS or physical AMD claim follows from restoring this code.
