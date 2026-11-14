"""Synthetic Maxwell programs authored from public Ryujinx decoder field definitions.
No game shader bytes. Each stores the result to shared memory so it remains live.
"""
import re
import struct
from pathlib import Path


def programs(donor):
    table = (Path(donor) / 'tools/vendor/ryujinx/src/Ryujinx.Graphics.Shader/Decoders/InstTable.cs').read_text(encoding='utf-8')
    def op(emitter):
        pattern = re.search(r'Add\("([01x]+)",[^\n]*InstEmit\.' + emitter + r'\s*,', table).group(1)
        assert len(pattern) == 64
        return int(pattern.replace('x', '0'), 2) | (7 << 16)  # PT: unconditional.
    def pack(instructions):
        words = []
        for i in range(0, len(instructions), 3):
            words.append(0)  # Maxwell scheduling/control word every 32 bytes.
            words.extend(instructions[i:i+3])
        return struct.pack('<' + 'Q' * len(words), *words)
    a = op('S2r') | (33 << 20)  # R0 = thread ID X (dynamic).
    b = op('S2r') | (34 << 20) | 1  # R1 = thread ID Y.
    store = op('Sts') | (4 << 48) | (255 << 8) | 2  # shared[RZ] = R2, B32.
    exit_ = op('Exit') | 15  # Ccc.T, unconditional termination.
    cases = {
        'bfe_dynamic': op('BfeR') | (1 << 20) | 2,
        'bfe_signed_reverse': op('BfeR') | (1 << 48) | (1 << 40) | (1 << 20) | 2,
        'bfe_immediate_past_word': op('BfeI') | (0x1020 << 20) | 2,
        'bfi_dynamic': op('BfiR') | (1 << 20) | 2,
        'bfi_immediate_past_word': op('BfiI') | (0x1020 << 20) | 2,
        'shf_left_dynamic': op('ShfLR') | (2 << 37) | (1 << 20) | 2,
        'shf_right_dynamic_signed_cc': op('ShfRR') | (3 << 37) | (1 << 47) | (1 << 20) | 2,
        'shf_left_immediate_zero': op('ShfLI') | (1 << 39) | 2,
        'shf_right_immediate_zero': op('ShfRI') | (1 << 39) | 2,
    }
    return {key: pack([a, b, instruction, store, exit_]) for key, instruction in cases.items()}
