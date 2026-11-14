# FOTO-01: bounds of images bound to the pool

The AMD band hypothesis is still unconfirmed. A CPU fixture running the donor's
`bind_pool_memory` shows it can admit two colour images whose Vulkan requirements overlap
even though their NVN storage is contiguous: image A: NVN range `[0,64)`, Vulkan `[0,128)`;
image B: NVN and Vulkan `[64,128)`. The resolution checks the whole physical pool or
contiguous virtual span, not each texture's sub-allocations. Depth/stencil already rejects
the excess. This proves a condition the code admits; it does not prove that an AMD driver
produces those requirements, writes the excess or causes the user's photos. A repeatable
geometry does not rule out partial work or repeatable races either.

`newsnap/pool_bounds_adapt.py` provides an experiment without per-GPU selection. The
integrator must wire it into `adapt.py`; this module does not activate itself.

- Without the flag, it keeps the donor's decisions and logs the first 16 colour images and
  4 depth/stencil images per process with `req.size > guest_size`, rejections included.
  Separate budgets keep depth rejections from using up the colour evidence.
- `AC_SNAP_POOL_BOUNDS=1` also rejects colour images with that excess. Creation then uses
  its existing fallback of VMA-owned memory.
- Other values keep the original policy. The flag is latched at the first colour candidate
  with excess through an atomic publication; set it before starting the process, do not
  change it during the session.
- It adds no Vulkan queries, guest content reads or per-frame instrumentation. Atomic
  counters allow at most 20 lines in total, even under concurrency.

Each `pool_bounds:` line includes handle/address, NVN/Vulkan formats, NVN dimensions,
guest/required size, alignment, compatible types, selected memory type and the available
offset/span if it got that far. `span_known=0` means the zero offset/span are not an
observation. `decision` identifies the real exit; `bound=1` only appears after a successful
bind. The logs do not say which bytes of the range the driver uses internally, nor show that
another texture is alive there. The budget can run out before the photo; no later lines does
not mean no excess.

The VMA fallback does not guarantee a dedicated `VkDeviceMemory` allocation. It increases
`own_bytes`, takes part in the cache budget and eviction and may clear the image to zero on
initialisation. It also loses the implicit alias with the pool buffer or other images.
`alias_copy` keeps certain compatible aliases at the same base address through staging, not
all partial aliases or those with other bases. That is why the flag is experimental and off
by default; it is not an accepted AMD fix.

Vulkan's rules on overlapping ranges do not guarantee that non-linear images keep their
content merely by sharing memory. Reference:
[Vulkan Memory Aliasing](https://docs.vulkan.org/spec/latest/chapters/resources.html#resources-memory-aliasing).

Focused test: `python -m unittest tests.test_pool_bounds -v`. It compiles and runs the
adapted C function with simulated Vulkan/VMA: default/opt-in, depth/stencil, zero/exact size,
resolution, alignment, type, bind failure, order/number of calls and the concurrent log
limit. It does not simulate a GPU driver or measure real images. Missing: integrated native
build, RTX control and an A/B of the same route on AMD with verified identity.
