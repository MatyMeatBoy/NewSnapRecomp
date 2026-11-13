"""Exact generator/runtime seams for live guest libc jump continuations.

Copied as recomp/snap_jumps.py in the private staging tree. Public source holds
hashes and semantic adaptation only, never the original SDK machine code.
"""
import hashlib
import struct


_SAVE = ('setjmp', '_setjmp')
_RESUME = ('longjmp', '_longjmp')
_CODE = {
    'save': (56, '630cf50e447d51094dc37af5f8ce499047f05f29bffd8e7412d3f79c5a5f465b'),
    'resume': (64, 'd07e37cbe1c09612fd9b30fbfe4925241dd30a1d4dfb67e81253ae3c3a93772e'),
}


def _plt_slot(mod, address):
    offset = address - mod.base
    if offset < 0 or offset + 16 > len(mod.image):
        return None
    adrp, load, add, branch = struct.unpack_from('<4I', mod.image, offset)
    if (adrp & 0x9f00001f != 0x90000010 or load & 0xffc003ff != 0xf9400211 or
            add & 0xffc003ff != 0x91000210 or branch != 0xd61f0220):
        return None
    immediate = ((adrp >> 5 & 0x7ffff) << 2) | (adrp >> 29 & 3)
    if immediate & 1 << 20:
        immediate -= 1 << 21
    displacement = (load >> 10 & 0xfff) * 8
    if (add >> 10 & 0xfff) != displacement:
        return None
    return (address & ~0xfff) + immediate * 4096 + displacement


class JumpAnalysis:
    def __init__(self, mod, starts):
        self.mod = mod
        cached = getattr(mod, '_snap_jump_discovery', None)
        if cached is None:
            saves, save_entries, resume_entries, slots = set(), set(), set(), set()
            for name, _info, section, value, _size in mod.nso.syms:
                if section and name in _SAVE + _RESUME:
                    kind = 'save' if name in _SAVE else 'resume'
                    size, expected = _CODE[kind]
                    if hashlib.sha256(mod.image[value:value + size]).hexdigest() != expected:
                        raise ValueError(f'{mod.name}: unsupported {name} implementation; guest jump ABI changed')
                    (save_entries if kind == 'save' else resume_entries).add(mod.base + value)
            saves.update(save_entries)
            for offset, kind, symbol, _addend in mod.nso.relocs:
                if kind in (257, 1025, 1026) and mod.nso.syms[symbol][0] in _SAVE:
                    slots.add(mod.base + offset)
            if slots:
                saves.update(address for address in starts if _plt_slot(mod, address) in slots)
            cached = saves, save_entries, resume_entries
            mod._snap_jump_discovery = cached
        self.saves, self.save_entries, self.resume_entries = cached

    def function(self, instructions, entry, end):
        saves = {entry + 4 * index: instruction.target for index, instruction in enumerate(instructions)
                 if instruction.kind == 'bl' and instruction.target in self.saves}
        if any(instruction.kind == 'b' and instruction.target in self.saves for instruction in instructions):
            raise ValueError(f'{entry:#x}: tail setjmp requires a verified caller checkpoint')
        resume_at = entry + 60 if entry in self.resume_entries else None
        if resume_at is not None and not entry <= resume_at < end:
            raise ValueError(f'{entry:#x}: split longjmp body requires explicit adaptation')
        return FunctionJump(saves, entry in self.save_entries, resume_at)


class FunctionJump:
    def __init__(self, saves, save_entry=False, resume_at=None):
        self.saves = saves
        self.save_entry = save_entry
        self.resume_at = resume_at

    def call(self, target, address, spill, reload_call, function):
        prefix = f'c->x[30] = 0x{address + 4:x}ull; {spill}'
        if address not in self.saves:
            return prefix + f'{function}(c);{reload_call}'
        return (prefix + '{ SnapJumpCheckpoint *snap_point = snap_jump_arm(snap_scope, c, '
                f'0x{address + 4:x}ull); if (!plat_jmp_save(&snap_point->native)) {function}(c); }}')

    def rewrite(self, lines):
        if self.saves:
            lines = [line.replace('__attribute__((musttail)) return', 'return') for line in lines]
            lines.insert(2, '    SnapJumpScope *snap_scope __attribute__((cleanup(snap_jump_scope_cleanup))) = snap_jump_scope_enter(c);')
        if self.save_entry:
            lines.insert(2, '    snap_jump_check_save(c);')
        return lines


def edits():
    """Apply once to the pinned donor; root adaptation copies this module too."""
    return {
        'recomp/gen.py': [
            ('import regs  # noqa: E402', 'import regs  # noqa: E402\nfrom snap_jumps import JumpAnalysis  # noqa: E402'),
            ('        self.unsupported = Counter()', '        self.unsupported = Counter()\n        self.snap_jumps = JumpAnalysis(mod, starts)'),
            ('        labels, tables = self.scan(insns, entry, end)',
             '        labels, tables = self.scan(insns, entry, end)\n        jumpinfo = self.snap_jumps.function(insns, entry, end)'),
            ('        local = not all_labels', '''        if jumpinfo.saves and all_labels:
            raise ValueError(f'{entry:#x}: setjmp owner with unresolved redispatch is unsupported')
        local = not all_labels and not jumpinfo.saves'''),
            ("            if fp.used:\n                out.append('    ' + fp.decl())",
             "            if fp and fp.used:\n                out.append('    ' + fp.decl())"),
            ("                return f'c->x[30] = {hx(a + 4)}; {spill}{fname(t)}(c);{reload_call}'",
             '                return jumpinfo.call(t, a, spill, reload_call, fname(t))'),
            ("            elif k == 'br':\n                jt = tables.get(a)",
             "            elif k == 'br' and jumpinfo.resume_at == a:\n                emit(i, f'    {spill}c->pc = c->x[30]; snap_jump_resume(c);')\n            elif k == 'br':\n                jt = tables.get(a)"),
            ('        return out, refs', '        return jumpinfo.rewrite(out), refs'),
            ("'#include \"cpu.h\"\\n#include \"simd.h\"\\n\\n'",
             "'#include \"cpu.h\"\\n#include \"simd.h\"\\n#include \"snap_jump.h\"\\n\\n'"),
        ],
        'runtime/kernel.c': [
            ('#include "host.h"', '#include "host.h"\n#include "snap_jump.h"'),
            ('int kern_host_track;', 'int kern_host_track = 1; // Nonlocal guest returns require host-service depth tracking.'),
            ('    plat_aligned_free(t->cpu);', '    snap_jump_clear(t->cpu);\n    plat_aligned_free(t->cpu);'),
            ('static void thread_finish(RtThread *t) {', '''static void thread_finish(RtThread *t) {
    snap_jump_clear(t->cur);
    if (t->cur != t->cpu) snap_jump_clear(t->cpu);'''),
            ('        if (t->fiber) {   // on a guest fiber: unwind from the thread\'s own context (kern_fiber_switch resumes it)',
             '        if (t->fiber) {   // on a guest fiber: unwind from the thread\'s own context (kern_fiber_switch resumes it)\n            snap_jump_clear(t->cur);'),
            ('    } else if (f->host) {\n        plat_fiber_free(f->host);',
             '    } else if (f->host) {\n        snap_jump_clear(f->cpu);\n        plat_fiber_free(f->host);'),
            ('    plat_aligned_free(f->cpu);', '    snap_jump_clear(f->cpu);\n    plat_aligned_free(f->cpu);'),
        ],
    }
