"""Read-only static inspection of the imported Snap 2.0.1 `main` module, for the notes in docs/HIGH_FPS.md.

    python -m tools.dev.inspect_main <path to exefs/main> dis 925b60 925c60
    python -m tools.dev.inspect_main <main> callers 7a9a70          # bl/b sites and 8-byte data references
    python -m tools.dev.inspect_main <main> imports hid             # imported symbols by name, with their call sites
    python -m tools.dev.inspect_main <main> strings talk message    # printable strings containing a word
    python -m tools.dev.inspect_main <main> refs 0xb02ca9           # adrp+add / adr references to an address
    python -m tools.dev.inspect_main <main> addimm 4b8              # every `add xD, xN, #imm` (field offsets)

Needs `capstone` for `dis` and `addimm`. Addresses are offsets in this exact module. Nothing is written; do not
commit dumps of the module (CONTRIBUTING.md).
"""
import importlib.util
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from newsnap.upstream import UPSTREAM  # noqa: E402

TEXT_END = 0xa40000


def load(path):
    spec = importlib.util.spec_from_file_location('nso', UPSTREAM / 'recomp/nso.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    nso = module.Nso(Path(path))
    return nso, bytes(nso.image)


def u32(image, pc):
    return struct.unpack_from('<I', image, pc)[0]


def branch_target(image, pc):
    word = u32(image, pc)
    if word >> 26 not in (0b100101, 0b000101):
        return None
    offset = word & 0x3ffffff
    if offset & 0x2000000:
        offset -= 0x4000000
    return pc + offset * 4


def disassemble(image, lo, hi):
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
    return [(i.address, i.mnemonic, i.op_str) for i in Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(image[lo:hi], lo)]


def callers(image, target):
    code = [pc for pc in range(0, len(image) - 4, 4) if branch_target(image, pc) == target]
    pattern = struct.pack('<Q', target)
    data = [m.start() for m in re.finditer(re.escape(pattern), image) if m.start() % 8 == 0]
    return code, data


def adrp_page(word, pc):
    imm = (((word >> 5) & 0x7ffff) << 2) | ((word >> 29) & 3)
    if imm & 0x100000:
        imm -= 0x200000
    return (pc & ~0xfff) + (imm << 12)


def code_refs(image, address):
    refs = []
    for pc in range(0, TEXT_END, 4):
        word = u32(image, pc)
        if word & 0x9f000000 == 0x90000000 and adrp_page(word, pc) == address & ~0xfff:
            rd = word & 31
            for k in range(1, 6):
                nxt = u32(image, pc + 4 * k)
                if nxt & 0xffc00000 == 0x91000000 and (nxt >> 5) & 31 == rd and (nxt >> 10) & 0xfff == address & 0xfff:
                    refs.append(pc)
                    break
        elif word & 0x9f000000 == 0x10000000:
            imm = (((word >> 5) & 0x7ffff) << 2) | ((word >> 29) & 3)
            if imm & 0x100000:
                imm -= 0x200000
            if pc + imm == address:
                refs.append(pc)
    return refs


def imports(nso, image, words):
    slots = {}
    for offset, _type, symbol, _addend in nso.relocs:
        if symbol and symbol < len(nso.syms) and any(word in nso.syms[symbol][0] for word in words):
            slots[offset] = nso.syms[symbol][0]
    stubs = {}
    for pc in range(0, len(image) - 16, 4):   # adrp x16 ; ldr x17, [x16, #lo] ; add x16 ; br x17
        word, nxt = u32(image, pc), u32(image, pc + 4)
        if word & 0x9f00001f != 0x90000010 or nxt & 0xffc003ff != 0xf9400211:
            continue
        slot = adrp_page(word, pc) + (((nxt >> 10) & 0xfff) << 3)
        if slot in slots:
            stubs[pc] = slots[slot]
    calls = {}
    for pc in range(0, len(image) - 4, 4):
        target = branch_target(image, pc)
        if target in stubs:
            calls.setdefault(stubs[target], []).append(pc)
    return {name: calls.get(name, []) for name in sorted(set(slots.values()))}


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    nso, image = load(argv[0])
    command, args = argv[1], argv[2:]
    if command == 'dis':
        for address, mnemonic, operands in disassemble(image, int(args[0], 16), int(args[1], 16)):
            print(f'{address:x}: {mnemonic} {operands}')
    elif command == 'callers':
        for text in args:
            code, data = callers(image, int(text, 16))
            print(text, 'code', [hex(pc) for pc in code], 'data', [hex(pc) for pc in data])
    elif command == 'imports':
        for name, sites in imports(nso, image, args).items():
            print(name, [hex(pc) for pc in sites])
    elif command == 'strings':
        words = [word.lower().encode() for word in args]
        seen = set()
        for match in re.finditer(rb'[\x20-\x7e]{4,80}', image):
            text = match.group()
            if text not in seen and any(word in text.lower() for word in words):
                seen.add(text)
                print(hex(match.start()), text.decode())
    elif command == 'refs':
        for text in args:
            print(text, [hex(pc) for pc in code_refs(image, int(text, 16))])
    elif command == 'addimm':
        imm = int(args[0], 16)
        for pc in range(0, TEXT_END, 4):
            if u32(image, pc) & 0xfffffc00 == (0x91000000 | (imm << 10)):
                print(hex(pc), ' ; '.join(f'{m} {o}' for _a, m, o in disassemble(image, pc, pc + 24))[:170])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
