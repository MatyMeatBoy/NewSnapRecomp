# Original controller reference

`ultimate2c-sprite.png` is an exact copy of the owner's original controller
illustration from ReKHCoM. It is reused at the owner's explicit request; no
Nintendo/game ROM sprites were extracted or copied.

- Repository: https://github.com/MatyMeatBoy/ReKHCoM
- Reference: `release/v2.9-20261106`, commit `51edf7e`.
- Original path: `port/assets/controller/ultimate2c-sprite.png`.
- Local staging source: `build/controller-reference-rekhcom/ultimate2c-sprite.png`.
- SHA-256: `a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4`.
- Original dimensions: **104 × 72**; **48 opaque colours plus transparency**.

Provenance: user-owned original controller art supplied through the
owner's ReKHCoM project. This reuse follows the owner's authorization; it does
not assign a new standalone third-party/public-domain licence to the image.

The PNG is immutable here. `newsnap/controller_art.py` loads it with native
Tk `PhotoImage` and integer nearest-neighbour `zoom` (default 4×, 416 × 288).
Switch labels and input highlights are separate native Canvas items. The four
original Xbox letters and their irregular dark bevels are covered in the Canvas
with colours already present in the source palette. A clean pixel contour stays
within each original button's bounds; labels are A right, B bottom, X top, Y left.
Each letter has a clear pixel before the contour; the eight-pixel-high top button
uses a compact four-row X. The controller's outer silhouette is unchanged. Shoulder,
trigger, +/- and stick labels are UI overlays; only active-state highlighting
adds a UI accent colour. No edited raster or generated replacement is stored.

Default highlights describe **physical SDL positions**, not the user's current
game bindings. Optional mapping is explicitly `Switch label -> SDL button name`,
e.g. `{'A': 'south', 'B': 'east'}`. Raw joystick indices without an SDL gamepad
mapping are not guessed. Trigger activation follows the runtime threshold
`> 16384`; stick position dots show raw axis movement without changing it.
