# Ultrawide investigation (ULTRAWIDE-01)

Status: **not shipped** (0.8.6). A working 3D widening exists, but photos break.

## What works

Astral Chain's `wide` set (`third_party/astral/recomp/patches-v101.txt`, from TLin-Y's
aspect-ratio pchtxt) keeps the game's 16:9 targets, gives 16:9 lenses the window's ratio and
stretches the picture to the window. Snap's perspective builder is at `main+0x296400`
(`fdiv s2,s12,s0` = cot(fov/2), the same site the reference Snap recomp uses for FOV);
`main+0x296418` `fdiv s1,s2,s9` divides by the camera's aspect (`[x20,#0x12c]`), so s1 is the
X scale. A hook at `main+0x29641c` (`mov v0.s[0],v1.s[0]`, word `6e040420`) that sets
`s1 *= (16/9) / window_ratio` for 16:9 cameras, plus a stretched present, gives a correct,
wider 3D view in a 2520×1080 window (tested on the RX 6900 XT, photo route, exit 0).

## Why it was backed out

1. **Photos:** Snap captures the photo from the same frame. The thumbnail of a photo taken
   in ultrawide shows the whole wide view squeezed into 16:9, so saved photos would be
   distorted and scoring would change. A fix needs the capture frame to use the 16:9 lens
   (find the shutter/Capture3D frame and skip the widening for it) or a capture crop.
2. **HUD:** the interface is drawn into the same 16:9 target and gets stretched (elliptical
   reticle, wide portraits). A fix needs Snap's UI camera/orthographic projection, like
   Astral Chain's `rt_wide_view_x8` / `rt_wide_flat_w8` sites.

The code is in git history (commit "Ultrawide: widen 16:9 cameras…" on the 0.8.6 branch).
