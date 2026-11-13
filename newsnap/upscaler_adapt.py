"""Optional, explicitly fetched official SDK. The portable build needs no download."""
from pathlib import Path
import shutil


def edits():
    return {'tools/build_game.py': [
        ("    libs = [f'-L {cmd_path(DEPS / \"lib\")}']", "    sdk = os.environ.get('NEWSNAP_FSR_SDK')\n    if sdk and WIN:\n        rt_inc += f' -DNEWSNAP_FSR_SDK=1 -I {cmd_path(Path(sdk) / \"Kits/FidelityFX\")}'\n    libs = [f'-L {cmd_path(DEPS / \"lib\")}']"),
    ], 'runtime/cfg.c': [
        ('"off|auto|dlss|xess|fsr3"', '"off|auto|dlss|xess|fsr3|fsr4"'),
    ], 'runtime/vk_device.c': [
        ('#include "vk.h"', '#include "vk.h"\n#include "snap_fsr_sdk.h"'),
        ('    VkPhysicalDeviceMutableDescriptorTypeFeaturesEXT mut;   // XeSS (vk_xess.c) only', '''    VkPhysicalDeviceMutableDescriptorTypeFeaturesEXT mut;   // XeSS (vk_xess.c) only
#ifdef VK_KHR_compute_shader_derivatives
    VkPhysicalDeviceComputeShaderDerivativesFeaturesKHR fsr_derivatives;
#endif
#ifdef VK_KHR_cooperative_matrix
    VkPhysicalDeviceCooperativeMatrixFeaturesKHR fsr_coop;
#endif
#ifdef VK_EXT_shader_float8
    VkPhysicalDeviceShaderFloat8FeaturesEXT fsr_float8;
#endif'''),
        ('    // Graphics pipeline library: chained last so it can be dropped again when vk_caps_gpl declines it.', '''#ifdef VK_KHR_compute_shader_derivatives
    if (has_ext(ep, ne, VK_KHR_COMPUTE_SHADER_DERIVATIVES_EXTENSION_NAME) && n_ext < 80) {
        ext[n_ext++] = VK_KHR_COMPUTE_SHADER_DERIVATIVES_EXTENSION_NAME;
        CHAIN(fsr_derivatives, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COMPUTE_SHADER_DERIVATIVES_FEATURES_KHR);
    }
#endif
#ifdef VK_KHR_cooperative_matrix
    if (has_ext(ep, ne, VK_KHR_COOPERATIVE_MATRIX_EXTENSION_NAME) && n_ext < 80) {
        ext[n_ext++] = VK_KHR_COOPERATIVE_MATRIX_EXTENSION_NAME;
        CHAIN(fsr_coop, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_FEATURES_KHR);
    }
#endif
#ifdef VK_EXT_shader_float8
    if (has_ext(ep, ne, VK_EXT_SHADER_FLOAT8_EXTENSION_NAME) && n_ext < 80) {
        ext[n_ext++] = VK_EXT_SHADER_FLOAT8_EXTENSION_NAME;
        CHAIN(fsr_float8, VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT8_FEATURES_EXT);
    }
#endif
    // Graphics pipeline library: chained last so it can be dropped again when vk_caps_gpl declines it.'''),
        ('    vk_caps_driver(g_vk.phys);', '''    snap_fsr_sdk_int8_enabled = 0;
#ifdef VK_KHR_compute_shader_derivatives
    // The pinned SDK specifically identifies derivativeGroupLinear for its INT8 prepass.
    // Its provider query/create determines model compatibility; do not invent extra model requirements.
    snap_fsr_sdk_int8_enabled = c->fsr_derivatives.computeDerivativeGroupLinear;
#endif
    vk_caps_driver(g_vk.phys);'''),
    ], 'runtime/vk_dlaa.c': [
        ('#include "vk_fsr3.h"', '#include "vk_fsr3.h"\n#include "snap_fsr_runtime.h"'),
        ('enum { BK_NONE, BK_DLSS, BK_XESS, BK_FSR3 };', 'enum { BK_NONE, BK_DLSS, BK_XESS, BK_FSR3, BK_FSR4 };'),
        ('D.backend == BK_FSR3 ? vk_fsr3_available()', '(D.backend == BK_FSR3 || D.backend == BK_FSR4) ? snap_fsr_runtime_available(D.backend == BK_FSR4)'),
        ('bk == BK_FSR3 ? !vk_fsr3_failed() : 0;', '(bk == BK_FSR3 || bk == BK_FSR4) ? snap_fsr_runtime_available(bk == BK_FSR4) : 0;'),
        ('           : !strcmp(up, "fsr3") ? BK_FSR3', '           : !strcmp(up, "fsr3") ? BK_FSR3\n           : !strcmp(up, "fsr4") ? BK_FSR4'),
        ('           : !strcmp(up, "auto") ? (can(BK_DLSS) ? BK_DLSS : BK_FSR3)',
         '           : !strcmp(up, "auto") ? (can(BK_DLSS) ? BK_DLSS : can(BK_FSR4) ? BK_FSR4 : BK_FSR3)'),
        ('    if (bk == BK_FSR3) return vk_pipeline_push_fn() ? vk_fsr3_available() : !vk_fsr3_failed();',
         '    if (bk == BK_FSR3 || bk == BK_FSR4) return snap_fsr_runtime_available(bk == BK_FSR4);'),
        ('    if (!strcmp(up, "fsr3") || !strcmp(up, "auto")) return vk_fsr3_failed() && !can(BK_DLSS) ? 2 : 0;',
         '''    if (!strcmp(up, "fsr3")) return can(BK_FSR3) ? 0 : 2;
    if (!strcmp(up, "fsr4")) return can(BK_FSR4) ? 0 : 2;
    if (!strcmp(up, "auto")) return pick() != BK_NONE ? 0 : 2;'''),
        ('static void features_sweep(int all) {', 'static void features_sweep(int all) {\n    snap_fsr_runtime_sweep(all);'),
        ('    if (N.loaded) features_sweep(0);',
         '    snap_fsr_runtime_sweep(0); // reap FSR-only retirements even after temporal AA is switched off\n    if (N.loaded) features_sweep(0);'),
        ('static void free_size(struct Size *e) {', 'static void free_size(struct Size *e) {\n    snap_fsr_runtime_retire(e->out);'),
        ('static void sharpen(VkCommandBuffer cb, struct Size *e, VkImage *img, VkImageView *view) {',
         '#include "snap_fsr_runtime.inc"\n\nstatic void sharpen(VkCommandBuffer cb, struct Size *e, VkImage *img, VkImageView *view) {'),
        ('''    if (D.backend == BK_FSR3) {
        Fsr3Eval f = {.color = cv, .depth = zv, .mv = e->mv_view, .out = e->out_view, .w = w, .h = h, .ow = ow, .oh = oh,
                      .jx = jx, .jy = jy, .phases = jitter_phases(w, ow), .dt_ms = dt_ms, .reset = D.reset, .hdr = hdr};
        camera_planes(&f.near_z, &f.far_z, &f.fov_y);
        if (!vk_fsr3_evaluate(cb, &f)) return 0;   // off for the rest of the run (vk_fsr3.c)
    }''', '''    if (D.backend == BK_FSR3 || D.backend == BK_FSR4) {
        if (!snap_fsr_runtime_evaluate(cb, t, z, e, jx, jy, dt_ms, hdr, D.reset, D.backend == BK_FSR4, ex->fence)) return 0;
    }'''),
        ('    const VkCtx *c = vk_ctx();\n    for (int i = 0; i < 3; i++) {\n        struct Size *e = &D.sizes[i];',
         '    const VkCtx *c = vk_ctx();\n    snap_fsr_runtime_shutdown();\n    for (int i = 0; i < 3; i++) {\n        struct Size *e = &D.sizes[i];'),
        ('           : b == BK_FSR3 ? (up ? "FSR 3" : "FSR 3 Native AA")',
         '           : b == BK_FSR4 ? (up ? "FSR 4" : "FSR 4 Native AA")\n           : b == BK_FSR3 ? (up ? "FSR 3.1.6" : "FSR 3.1.6 Native AA")'),
    ]}


def stage_sdk(sdk_root, output):
    """Verify before packaging runtime binaries and their redistribution notices."""
    from tools.fetch_upscaler_sdk import FILES, PREFIX, verify
    sdk_root, output = Path(sdk_root), Path(output)
    if not verify(sdk_root):
        raise ValueError('FSR SDK does not match the pinned official files; run tools/fetch_upscaler_sdk.py')
    destination = output / 'upscalers'
    destination.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if name.endswith('.dll') or name in (PREFIX + 'docs/license.md', '3rdpartynotice.md'):
            shutil.copy2(sdk_root / name, destination / Path(name).name)
    return destination
