"""Reproducible source overlay for the initial Snap runtime bring-up.

Does not change upstream or apply any of its game instruction patches.
"""
import difflib
import shutil
from pathlib import Path

from .upstream import ROOT, UPSTREAM


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
        ],
        'runtime/kernel.c': [
            ('#define MAIN_STACK (1ull << 20)', '#define MAIN_STACK 0x4000ull'),
        ],
        'runtime/frame_rate.c': [
            ('int on = hz >= 60;', 'int on = hz >= 60 && rt_patch_set("fps60") >= 0; // Snap has no inherited timing patch.'),
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
        write_changed(destination / name, text)
        diff.extend(difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True),
                                         fromfile='a/' + name, tofile='b/' + name))
    write_changed(destination / 'VERSION', '0.1.0-dev\n')
    for overlay in (ROOT / 'newsnap/overlays').glob('*'):
        if overlay.is_file():
            write_changed(destination / 'runtime' / overlay.name, overlay.read_text(encoding='utf-8'))
    shutil.copy2(UPSTREAM / 'LICENSE', destination / 'LICENSE')
    if patch_output:
        write_changed(Path(patch_output), ''.join(diff))
    return destination
