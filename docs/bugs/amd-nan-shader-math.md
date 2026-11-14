# NaN in translated shaders on AMD: a guide for Switch recomps

2026-11-14 · MatyMeatBoy. Real case: CRISTAL-01 (black Crystabloom on the RX 6900 XT). This guide
applies to any port that translates Maxwell shaders to SPIR-V (the Ryujinx translator, yuzu
and derivatives) and sees black objects, halos or blotches only on AMD.

## Symptom

- An object, or part of it, comes out **solid black** on AMD and fine on NVIDIA.
- With temporal antialiasing (FSR, DLAA, TAA) a black **halo** or ghosting also appears around
  it, because the history drags the NaN into later frames.
- In severe cases, a NaN that reaches a blur or reduction pass spreads over the whole screen.

## Cause

The Switch GPU (Maxwell) and Vulkan treat special values differently:

| Operation | Maxwell (Switch) | SPIR-V the translator emits | AMD | NVIDIA |
|---|---|---|---|---|
| `min/max` with a NaN | returns the other operand (FMNMX) | `FMin/FMax`: **undefined** | may return NaN | returns the other |
| `saturate(NaN)` | 0 (`.SAT`) | `FClamp(x,0,1)`: **undefined** | may give NaN | 0 |
| `sqrt`/`log2` of a near-zero | the math gives ≥ 0 | `Sqrt/Log2` | sometimes −ε, and sqrt/log2 of −ε is NaN | usually 0 |

The last case comes from precision: an `fma(dot(n, l), 0.5, 0.5)` with normalised vectors can
come out slightly negative on AMD and exactly 0 on NVIDIA.

## How to diagnose it (without guessing)

1. Dump the frame with the defect on screen (`AC_DUMP_KEY=1`, F12).
2. In `images.txt`, find the **first pass with `nan N`** above 0. The clean pass before and
   the next one with NaN bound the guilty draw.
3. In `passes.txt`, that pass gives the shader ids (`vs`/`fs`). The binaries are
   `sh_<id>.spv` in one of the session's dumps.
4. Decompile with `spirv-cross --vulkan-semantics` and count
   `FClamp/FMin/FMax/Sqrt/InverseSqrt/Log2` (`spirv-dis`).
5. `AC_DUMP_UBO=48` adds the constant buffers, in case the NaN comes from data and not from
   the math.

## Fix applied in NewSnap (`newsnap/spirv_nminmax_adapt.py`)

Each module is rewritten right before `vkCreateShaderModule` (`make_module` in
`vk_pipeline.c`). It does not touch the translator or its cache:

- `AC_SPIRV_NMINMAX`: GLSL.std.450 `FMin`(37)/`FMax`(40)/`FClamp`(43) become
  `NMin`(79)/`NMax`(80)/`NClamp`(81). This is Maxwell's exact semantics.
- `AC_SPIRV_DOMAIN_CLAMP`: `NMax(x, 0)` is inserted before `Sqrt`(31)/`InverseSqrt`(32)/
  `Log2`(30), with one null constant per type.
- Both on by default on AMD and off elsewhere, so NVIDIA keeps giving exactly the same
  result. Cost: the first start recompiles the pipelines in the driver.
- Validation: `spirv-val --target-env vulkan1.3` over the 89 distinct shaders from the owner's
  dumps, with no errors. In game: 0 passes with NaN and the crystal correct.

## Mistakes to avoid

- Do not "fix" the NaN at the end of the shader or in the output pass: it hides the cause and
  leaves the lighting wrong.
- Do not order −0 below +0 in `NMin/NMax`: ocarina-recomp tried it and the image came out
  entirely white.
- Do not change the math on NVIDIA without need: there the result already matches the
  Switch.
- One good session does not attribute the cause. To know which of the two settings fixes it,
  turn one off at a time (`AC_SPIRV_NMINMAX=0` / `AC_SPIRV_DOMAIN_CLAMP=0`).

## Sources (equivalent cases in other projects)

- Lichii, issue #325 (AMD, Ocarina of Time: haze and bright water from NaN in
  FMin/FMax/FClamp): <https://github.com/zortos293/Lichii/issues/325>
- Lichii, PR #432 (min/max/clamp with defined NaN): <https://github.com/zortos293/Lichii/pull/432>
- Savage Wind Recomp, PR #153 (NMin/NMax/NClamp; measured on AMD with RADV; not integrated
  because of cache cost and no measurable gain on NVIDIA):
  <https://github.com/Revivedx/SavageWindRecomp/pull/153>
- ocarina-recomp, issue #49 (RX 9070 XT: black silhouettes fixed with `Sqrt(NMax(x, 0))`;
  −0/+0 ordering reverted): <https://github.com/sostenesfreitas/ocarina-recomp/issues/49>
- Direct3D floating-point rules (min/max return the non-NaN operand):
  <https://learn.microsoft.com/windows/uwp/graphics-concepts/floating-point-rules>
