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
        'tools/ffx_sdk.py': [
            ("GLSL_BIN = Path(r'C:\\msys64\\ucrt64\\bin')", "GLSL_BIN = Path(os.environ.get('NEWSNAP_SHADER_TOOLS', r'C:\\msys64\\ucrt64\\bin'))"),
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
    shutil.copy2(UPSTREAM / 'LICENSE', destination / 'LICENSE')
    if patch_output:
        write_changed(Path(patch_output), ''.join(diff))
    return destination
