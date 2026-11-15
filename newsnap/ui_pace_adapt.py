"""UI-HZ-01: declare the interface pacing helpers for the guest patch table.

The patch set (patches/snap-2.0.1-ui-pace.txt) and the overlay (overlays/snap_ui_pace.c) hold
the interface's Flash-style timelines at 60 steps a second of real time when the game runs above
60 fps. Nothing here changes behaviour by itself.
"""


def edits():
    return {'runtime/cpu.h': [
        ('typedef void (*GuestFn)(Cpu *);',
         'void snap_ui_pace_begin(Cpu *c);\nvoid snap_ui_pace_movie(Cpu *c);\n'
         'typedef void (*GuestFn)(Cpu *);'),
    ]}
