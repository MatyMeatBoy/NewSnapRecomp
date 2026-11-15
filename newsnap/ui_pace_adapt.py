"""UI-HZ-01: declare the interface pacing helpers for the guest patch table.

The patch set (patches/snap-2.0.1-ui-pace.txt) and the overlay (overlays/snap_ui_pace.c) make the
interface handler's logic, its Flash-style timelines and its per-frame event run 60 times a second
of real time above 60 fps, while the interface is still drawn on every frame. Nothing here changes
behaviour by itself.
"""


def edits():
    return {'runtime/cpu.h': [
        ('typedef void (*GuestFn)(Cpu *);',
         'void snap_ui_pace_enter(Cpu *c);\nvoid snap_ui_pace_event(Cpu *c);\nvoid snap_ui_pace_pad(Cpu *c);\n'
         'typedef void (*GuestFn)(Cpu *);'),
    ]}
