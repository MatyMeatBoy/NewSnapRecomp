"""Reproducible source overlay for the initial Snap runtime bring-up.

Does not change upstream or apply any of its game instruction patches.
"""
import difflib
import shutil
from pathlib import Path

from .upstream import ROOT, UPSTREAM
from .input_adapt import edits as input_edits
from .output_adapt import edits as output_edits
from .jump_adapt import edits as jump_edits
from .temporal_adapt import edits as temporal_edits
from .upscaler_adapt import edits as upscaler_edits
from .texture_adapt import adapt_texture_source
from .neutral_adapt import edits as neutral_edits
from .vrr_adapt import edits as vrr_edits
from .menu_adapt import edits as menu_edits
from .color_transfer_adapt import edits as color_transfer_edits
from .photo_readback_adapt import edits as photo_readback_edits
from .camera_input_adapt import edits as camera_input_edits
from .graphics_effects_adapt import edits as graphics_effects_edits
from .random_range_adapt import edits as random_range_edits
from .console_adapt import edits as console_edits
from .branding_adapt import edits as branding_edits
from .present_trace_adapt import edits as present_trace_edits
from .pool_bounds_adapt import edits as pool_bounds_edits
from .bc_block_views_adapt import edits as bc_block_views_edits
from .hid_six_axis_adapt import edits as hid_six_axis_edits
from .spirv_nminmax_adapt import edits as spirv_nminmax_edits
from .windowed_present_adapt import edits as windowed_present_edits
from .crc_isa_adapt import edits as crc_isa_edits
from .xlate_semantics_adapt import edits as xlate_semantics_edits, stage_patches as stage_xlate_patches
from .version import VERSION


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'Upstream changed: expected one occurrence of {before[:65]!r}')
    return text.replace(before, after, 1)


def write_changed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding='utf-8') == text:
        return
    path.write_text(text, encoding='utf-8', newline='\n')


def adapt_sources(destination, *, patch_output=None):
    destination = Path(destination)
    edits = {
        'recomp/layout.py': [
            ("ROMFS_BASES = {", "ROMFS_BASES = {\n    'snap': 0,  # No Astral Chain fixed-address RomFS mapping in Snap."),
            ("return romfs.stat().st_size if romfs.exists() else 0", 'return 0  # Snap uses nn::fs; a fixed image mapping has not been observed.'),
        ],
        'runtime/boot.c': [
            ('"_ZN2nn4init5StartEmmPFvvES2_"', '"_ZN2nn4init5StartEmmPFvvES2_S2_"'),
            ('stack != 0x100000', 'stack != 0x4000'),
            ('kernel.c builds 44, 0, 0x100000', 'kernel.c builds 44, 0, 0x4000'),
            ('if (!rt_config()->shot) vk_pipeline_async_enable();', 'vk_pipeline_async_enable(); // Record/prewarm even for deterministic screenshots.'),
            ('if (rt_config()->seconds) return;   // --seconds: the run goes on into the game', '''extern void snap_decode_requested(Cpu *cpu);
        snap_decode_requested(c);
        if (rt_config()->seconds) return;   // --seconds: the run goes on into the game'''),
        ],
        'runtime/ov_fsp.c': [
            ('switch (rq->cmd) {', '''switch (rq->cmd) {
    case 202: // OpenDataStorageByDataId must return an IStorage object on success.
        // No system-data mount exists yet. Success without an object made Snap
        // dereference a null storage while opening the naming dictionary.
        rt_log("fsp-srv: system-data storage unavailable; no object returned");
        rs->result = 0x7d402u; // nn::fs::ResultTargetNotFound
        return;'''),
        ],
        'runtime/gfx_present.c': [
            ('if (restart) {\n        plat_setenv("AC_REEXEC", NULL);',
             'if (restart) {\n        const char *launcher = getenv("NEWSNAP_LAUNCHER");\n        if (launcher && !strcmp(launcher, "1")) plat_exit(75); // Parent keeps profile lock across restart.\n        plat_setenv("AC_REEXEC", NULL);'),
            (': !strcmp(e, "immediate") ? VK_PRESENT_MODE_IMMEDIATE_KHR : VK_PRESENT_MODE_FIFO_KHR;',
             ': !strcmp(e, "immediate") ? VK_PRESENT_MODE_IMMEDIATE_KHR\n                          : !strcmp(e, "fifo_relaxed") ? VK_PRESENT_MODE_FIFO_RELAXED_KHR : VK_PRESENT_MODE_FIFO_KHR;'),
            ('got == VK_PRESENT_MODE_IMMEDIATE_KHR ? "immediate" : "fifo";',
             'got == VK_PRESENT_MODE_IMMEDIATE_KHR ? "immediate" : got == VK_PRESENT_MODE_FIFO_RELAXED_KHR ? "fifo_relaxed" : "fifo";'),
            ('void gfx_window_closed(void) {', '''void gfx_window_closed(void) {
    extern int snap_exit_begin_close(void);
    if (!snap_exit_begin_close()) return;'''),
        ],
        'runtime/cpu.h': [
            ('typedef void (*GuestFn)(Cpu *);', 'typedef void (*GuestFn)(Cpu *);\nvoid snap_render_select(Cpu *c); // Verified Snap render graph selection hook.\nvoid snap_supersample_resize(Cpu *c); // Opt-in engine resize prototype.'),
        ],
        'runtime/ov_system.c': [
            ('static void location_name(char out[0x24])', 'void ov_time_location(char out[0x24])'),
            ('location_name(n.location);', 'ov_time_location(n.location);'),
            ('static void ov_to_calendar(Cpu *c)', 'void ov_time_calendar(Cpu *c)'),
            ('              ov_to_calendar);', '              ov_time_calendar);'),
        ],
        'runtime/cfg.c': [
            ('{"LANG", "", "ja|en-US|fr|de|it|es|zh-CN|ko|nl|pt|ru|zh-TW|en-GB|fr-CA|es-419|zh-Hans|zh-Hant|pt-BR", RESTART}',
             '{"LANG", "", "en-US|ja|fr|de|es-419|es|it|fr-CA|ko|zh-Hant|zh-Hans", RESTART}'),
            ('{"ANISO", "auto", "auto|game|2|4|8|16", RESTART}', '{"ANISO", "game", "game|2|4|8|16", RESTART}'),
            ('{"ASPECT", "wide", "fit|stretch|wide", LIVE}', '{"ASPECT", "fit", "fit|stretch", LIVE}'),
            ('"game|50|67|75|100|125|150|200"', '"game|50|60|70|80|90|100|125|150|200"'),
            ('"mailbox|fifo|immediate"', '"mailbox|fifo|fifo_relaxed|immediate"'),
        ],
        'runtime/vk_pipeline.c': [
            ('int vk_pipeline_async_on(void) { return A.on; }', 'int vk_pipeline_async_on(void) { return A.on && !rt_config()->shot; }'),
            ('return graphics(s, info, A.on, pending, wait_ms);', 'return graphics(s, info, vk_pipeline_async_on(), pending, wait_ms);'),
        ],
        'runtime/kernel.c': [
            ('#define MAIN_STACK (1ull << 20)', '#define MAIN_STACK 0x4000ull'),
        ],
        'runtime/frame_rate.c': [
            ('int on = hz >= 60;', 'int on = hz >= 60 && rt_patch_set("fps60") >= 0; // Snap has no inherited timing patch.'),
            ('if (on == fps60_on && fps_hz) return;', 'if (on == fps60_on && fps_hz == (hz >= 60 ? 60 : 30)) return;'),
            ('fps_hz = on ? 60 : 30;', 'fps_hz = hz >= 60 ? 60 : 30; // Presentation cap is independent of game timing patches.'),
            ('on ? " (60 fps patch)" : " (30 fps)"', 'on ? " (60 fps patch)" : " cap (native game timing)"'),
            ('if (!fps60_on) return;\n    uintptr_t base', 'if (!fps60_on || rt_patch_set("fps60") < 0) return;\n    uintptr_t base'),
        ],
        'runtime/nvn_api_core.c': [
            ('HOST_OBSERVER("_ZN2nn2os15ReleaseReadLockEPNS0_20ReaderWriterLockTypeE", obs_release_read);',
             '// Snap: Astral Chain/TotK address-specific LOD observer intentionally not registered.'),
        ],
        'runtime/gfx_window_win.c': [
            ('L"Astral Chain Recomp"', 'L"NewSnapRecomp"'),
        ],
        'runtime/nvn_procs.inc': [
            ('NVN_PROC(nvnDeviceInitialize)', 'NVN_PROC(nvnSetExternalDebuggerEnabledNVX)\nNVN_PROC(nvnDeviceInitialize)'),
        ],
        'runtime/nvn_api_obj.c': [
            ('return ticks * 1000000000ull / VSYNC_HZ;', '''uint64_t native_period = ticks * 1000000000ull / VSYNC_HZ;
    uint64_t cap_period = frame_step_cap_ns();
    return native_period > cap_period ? native_period : cap_period;'''),
            ('if (o->serial) gfx_backend()->program_release(o);', '''if (o->serial) gfx_backend()->program_release(o);
    free(o->control_copy);
    o->control_copy = NULL;'''),
            ('''    prog_release(o);
    o->nstage = (uint32_t)n;
    if (n) memcpy(o->sd, sd, (size_t)n * sizeof *sd);''', '''    // NVN consumes control metadata at SetShaders. Snap can release its archive
    // metadata afterwards, so the deferred renderer needs a program-owned copy.
    uint8_t *copy = n ? malloc((size_t)n * 0x880) : NULL;
    if (n && !copy) return 0;
    for (int i = 0; i < n; i++) {
        if (!sd[i].control) { free(copy); return 0; }
        memcpy(copy + (size_t)i * 0x880, sd[i].control, 0x880);
    }
    prog_release(o);
    o->control_copy = copy;
    o->nstage = (uint32_t)n;
    for (int i = 0; i < n; i++) {
        o->sd[i] = sd[i];
        o->sd[i].control = copy + (size_t)i * 0x880;
    }'''),
        ],
        'runtime/nvn_obj.h': [
            ('NVNshaderData sd[6]; uint64_t serial; } prog_t;', 'NVNshaderData sd[6]; uint64_t serial; void *control_copy; } prog_t;'),
        ],
        'tools/ffx_sdk.py': [
            ("GLSL_BIN = Path(r'C:\\msys64\\ucrt64\\bin')", "GLSL_BIN = Path(os.environ.get('NEWSNAP_SHADER_TOOLS', r'C:\\msys64\\ucrt64\\bin'))"),
        ],
        'runtime/ipc.c': [
            ('#include "ipc.h"', '#include "ipc.h"\n#include "ipc_frame.h"'),
            ('s->domain = 1;\n        return;', 's->domain = 1;\n        { uint32_t root = 1; IPC_OUT(rs, root); }\n        return;'),
            ('''        uint32_t h[4];
        memcpy(h, payload, 16);
        if (h[0] != CMIF_IN_MAGIC) {
            ipc_backtrace();
            rt_fatal("ipc: %s: CMIF magic %#x (domain sessions are not served)", s->name, h[0]);
        }
        rq.cmd = h[2];
        rq.data = payload + 16;
        rq.data_size = payload + 16 <= end ? (uint32_t)(end - payload - 16) : 0;
        if (s->domain && rq.type != T_CONTROL && rq.type != T_CONTROL_CTX && rq.data_size >= 16) {
            const uint32_t *dh = (const uint32_t *)rq.data;
            if ((dh[0] & 0xff) == 2) return;   // CloseVirtualHandle
            rq.data += 16;
            rq.data_size -= 16;
            domain = 1;
        }''', '''        SnapCmif frame;
        int is_domain = s->domain && rq.type != T_CONTROL && rq.type != T_CONTROL_CTX;
        if (payload > end || !snap_cmif_frame(payload, (size_t)(end - payload), is_domain, &frame)) {
            ipc_backtrace();
            rt_fatal("ipc: %s: invalid CMIF/domain frame", s->name);
        }
        if (frame.close) return;
        rq.cmd = frame.command;
        rq.data = frame.data;
        rq.data_size = frame.size;
        domain = frame.domain;'''),
        ],
        'runtime/gfx_shader.c': [
            ('if (!code || r->length > code_size || c1_off > r->length || skip >= r->length) return fail("bad control section", NULL), 0;',
             '''if (!code || r->length > code_size || c1_off > r->length || skip >= r->length) {
        static int snap_bad_controls;
        if (snap_bad_controls++ < 12)
            rt_log("Snap shader control: stage %d, code %p, available %llu, length %u, c1 %u, skip %llu",
                   stage, code, (unsigned long long)code_size, r->length, c1_off, (unsigned long long)skip);
        return fail("bad control section", NULL), 0;
    }'''),
        ],
        'runtime/memory.c': [
            ('if (!in_heap && !in_alias) return R_INVALID_REGION;', '''int in_module_data = 0;
    int snap_module = module_index(src);
    if (snap_module >= 0) {
        const RtLoaded *m = ldr_module(snap_module);
        in_module_data = inside(src, n, (RtRange){m->base + m->data_off, m->size - m->data_off});
    }
    if (!in_heap && !in_alias && !in_module_data) return R_INVALID_REGION;'''),
            ('unsigned found = nstack_maps;', '''if (in_module_data) {
        const RtLoaded *m = ldr_module(snap_module);
        for (uint64_t off = src - m->base; off < src - m->base + n; off += PAGE) {
            if (module_page_perm(snap_module, off) != PERM_RW) {
                r = R_INVALID_STATE;
                goto out;
            }
        }
    }
    unsigned found = nstack_maps;'''),
            ('.state = ST_NORMAL, .perm = PERM_NONE, .attr = 4', '.state = module_index(m->src) >= 0 ? ST_CODEDATA : ST_NORMAL, .perm = PERM_NONE, .attr = 4'),
            ('r.state == ST_NORMAL ? m->src : 0;', '(r.state == ST_NORMAL || r.state == ST_CODEDATA) ? m->src : 0;'),
        ],
        'tools/build_game.py': [
            ("EXE = 'astralchain.exe' if WIN else 'astralchain'", "EXE = 'newsnap.exe' if WIN else 'newsnap'"),
        ],
    }
    for name, changes in jump_edits().items():
        edits.setdefault(name, []).extend(changes)
    for name, changes in input_edits().items():
        edits.setdefault(name, []).extend(changes)
    for name, changes in output_edits().items():
        edits.setdefault(name, []).extend(changes)
    for adapter in (temporal_edits, upscaler_edits, neutral_edits, vrr_edits,
                    menu_edits, color_transfer_edits, photo_readback_edits, camera_input_edits,
                    graphics_effects_edits, random_range_edits, console_edits, branding_edits,
                    present_trace_edits, pool_bounds_edits, crc_isa_edits, xlate_semantics_edits,
                    bc_block_views_edits, hid_six_axis_edits, spirv_nminmax_edits,
                    windowed_present_edits):
        for name, changes in adapter().items():
            edits.setdefault(name, []).extend(changes)
    for folder in ('runtime', 'recomp', 'tools'):
        for src in (UPSTREAM / folder).rglob('*'):
            relative = src.relative_to(UPSTREAM)
            if not src.is_file() or '__pycache__' in src.parts or relative.as_posix() in edits:
                continue
            dst = destination / relative
            if not dst.is_file() or dst.stat().st_size != src.stat().st_size or dst.read_bytes() != src.read_bytes():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    diff = []
    for name, changes in edits.items():
        original = (UPSTREAM / name).read_text(encoding='utf-8')
        text = original
        for before, after in changes:
            text = replace_once(text, before, after)
        if name == 'runtime/vk_texture.c':
            text = adapt_texture_source(text)
        write_changed(destination / name, text)
        diff.extend(difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True),
                                         fromfile='a/' + name, tofile='b/' + name))
    stage_xlate_patches(destination)
    write_changed(destination / 'VERSION', VERSION + '\n')
    write_changed(destination / 'recomp/snap_jumps.py', (ROOT / 'newsnap/jump_adapt.py').read_text(encoding='utf-8'))
    for overlay in (ROOT / 'newsnap/overlays').glob('*'):
        if overlay.is_file():
            write_changed(destination / 'runtime' / overlay.name, overlay.read_text(encoding='utf-8'))
    # Keep the donor resource filename expected by its build rule, but embed
    # this project's original camera artwork in the actual game executable.
    shutil.copy2(ROOT / 'assets/icons/newsnap.ico', destination / 'runtime/astralchain.ico')
    shutil.copy2(UPSTREAM / 'LICENSE', destination / 'LICENSE')
    if patch_output:
        write_changed(Path(patch_output), ''.join(diff))
    return destination
