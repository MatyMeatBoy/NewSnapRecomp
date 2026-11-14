# Lead for FOTO-01: colour images bound to pool memory

2026-11-13 · MatyMeatBoy · **Hypothesis not checked on AMD.** Touches no reserved files; it is an
observation for whoever owns FOTO-01.

> **Note (added after receiving the AMD log):** the log near the 22:39 screenshot suggests an
> earlier runtime, without a hash that pins the exact identity (see
> `keyboard-after-photo.md`). The version of the 16:53 screenshot is not established.
> **The test must be repeated with an identified runtime on AMD.** The hypothesis below is
> still testable (image binding to the pool did not change between versions), but the first
> step is to repeat the test with the real 0.5.

## New observations

1. **The band pattern is identical in two different photos.** The 16:53 screenshot
   (`clipboard-b8af3c5e`) and the 22:39 one (`rx6900xt-0.5/album-bands-amd.png`) show
   different content but the same valid and black cells, in the same positions. This fits a
   memory layout; a deterministic race or partial work is not ruled out either. The
   measurement of the first screenshot is in `photo-bands-cpu.md` (15 bands of ≈48 rows,
   contiguous valid runs).
2. **A Pikachu photo shows complete on the evaluation screen** (`evaluation-good-amd.png`).
   The slot/JPEG identity and the specific textures still need checking; the single
   screenshot does not show they are the same bytes.
3. On the RTX 4060 the recorded transfers are 1080×720 and 240×200 in format 37 (RGBA8),
   with no source/buffer differences (the RTX tester's traces).

## The point in the code that fits

`vk_texture.c`, `bind_pool_memory`: an image whose storage is in a GPU-only pool is **bound
inside the pool's memory**, at the address the game gave it. The donor already documents the
risk on RDNA2 (the RX 6900 XT's family): the driver asks for more bytes for the image than
its NVN storage, and the tail falls on the next texture in the heap. The current guard only
covers depth/stencil:

```c
if ((e->f.depth || e->f.stencil) && req.size > guest_size) return 0;
```

The donor's comment says colour images «stay in place» because on an RX 9070 the GPU was not
seen writing the excess. That has not been measured on RDNA2 or with Snap's sizes (1080×720
and 240×200 are not Astral Chain sizes). If on the RX 6900 XT `req.size > guest_size` for a
colour image, two `VkImage`s are bound to overlapping memory: Vulkan leaves their content
undefined as soon as one is written, and the result would be exactly a fixed pattern in the
driver's tile order.

## How to check it without assuming anything

- **Measurement (decisive, cheap):** log on each bind attempt `addr`, size, format,
  `req.size`, `req.alignment`, `guest_size` and whether it was bound. On NVIDIA it gives the
  baseline; on AMD it tells whether any colour image on the photo route exceeds its storage.
  Opt-in diagnostics, no behaviour change.
- **A/B experiment:** a switch that binds no image whose `req.size` exceeds `guest_size`
  (the same rule as depth, with no per-vendor exception). The «own memory» fallback already
  exists and is used when alignment or memory type fail. If the bands disappear on AMD with
  the switch and come back without it, the cause is established.
- **RTX control:** force own memory for every colour image and repeat the 540 s route; it
  validates that the fallback does not break photos, evaluation or the tutorial before asking
  the owner.

## Limits

- There is no measurement of `req.size` on AMD: the hypothesis may be false.
- It does not by itself explain the saturated colour (COLOR-01).
- Which texture the selection screen uses has not been checked.
