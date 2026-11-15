# Ultrawide (ULTRAWIDE-01)

Status: **experimental, shipped in 0.8.9** (`aspect = ultrawide`, launcher «Ultrawide · vista más
ancha (experimental)»). Off unless chosen.

## How it works

Astral Chain's `wide` set (`third_party/astral/recomp/patches-v101.txt`, from TLin-Y's aspect-ratio
pchtxt) keeps the game's 16:9 targets, gives 16:9 lenses the window's ratio, stretches the picture
to the window and keeps the interface in the middle 16:9. Snap does the same
(`newsnap/overlays/snap_wide.c`, `newsnap/wide_adapt.py`, `patches/snap-2.0.1-wide.txt`):

- **3D:** Snap's perspective builder is at `main+0x296400` (`fdiv s2,s12,s0` = cot(fov/2), the
  reference Snap recomp's FOV site); `main+0x296418` `fdiv s1,s2,s9` divides by the camera's aspect
  (`[x20,#0x12c]`). A hook at `main+0x29641c` divides s1 by k = window ratio / (16/9) for 16:9
  cameras only.
- **Photos:** Snap captures a photo by drawing the tonemapped scene (full-size RGBA8_SRGB) into the
  1080×720 photo and the 360×240 thumbnail picture. In those passes the scene is replaced by its
  middle 1/k stretched back to full width (vkCmdBlitImage): the picture the 16:9 lens makes.
- **Interface:** the pass that draws the HUD into that same image (through a UNORM view) gets its
  viewport and scissor narrowed to the middle 1/k, so after the stretch the HUD keeps its
  proportions, centred.
- **Menus:** a frame without a widened camera is shown 16:9 with bars instead of stretched.

## Tested (RX 6900 XT, 2520×1080 window, photo route 450 s)

Exit 0, 0 validation errors in both `fit` and `ultrawide`. Wider 3D in the expedition and the lab;
HUD proportional and centred; the photo preview shows the usual 16:9 framing; menus with bars.

## Limits

- Scores were not compared on the same shot: the scripted route fires the shutter at different
  moments in each run (pose 738 vs 500, and earlier normal runs also gave 500). The reference Snap
  recomp found the scoring camera's angle at another site (`main+0x38cdbc`), which this hook does
  not touch; photos are captured from the 16:9 view. The owner accepted score equivalence on
  2026-11-14 until an issue reports otherwise.
- The photo's horizontal detail is the middle 1/k of the scene (about 76 % at 21:9) stretched back;
  higher internal resolution compensates.
- Full-screen effects drawn in the interface pass (fades) cover the middle 16:9 only.
- Not tested on RTX.
