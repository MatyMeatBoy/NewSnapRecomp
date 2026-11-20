"""Pinned Recomp Achievements SDK, used exclusively by the native game."""
from pathlib import Path
import shutil

from .upstream import ROOT
from .version import VERSION


def edits():
    return {
        'runtime/main.c': [
            ('    log_open(!mode);', '    log_open(!mode);\n    if (!mode || !strcmp(mode, "--boot")) {\n        extern void snap_achievements_init(void);\n        snap_achievements_init();\n    }'),
        ],
        'runtime/nvn_api_obj.c': [
            ('    frame_step_present(slot, o->interval);', '    { extern void snap_achievements_frame(void); snap_achievements_frame(); }\n    frame_step_present(slot, o->interval);'),
        ],
        'runtime/fs_host.c': [
            ('    if (!r) save_mounts++;', '    if (!r) {\n        save_mounts++;\n        // Conservative load boundary: successful save mount, not a story/progress event.\n        extern void snap_achievements_save_loaded(void);\n        snap_achievements_save_loaded();\n    }'),
            ('           nfiles - linked, bytes / 1048576.0, linked, (plat_now_ns() - t0) / 1e6, waits ? "; waits in save-tx" : "");\n    return 0;',
             '           nfiles - linked, bytes / 1048576.0, linked, (plat_now_ns() - t0) / 1e6, waits ? "; waits in save-tx" : "");\n    // Only changed data durably committed in this live process; no story/progress inference.\n    { extern void snap_achievements_event(const char *); snap_achievements_event("save_committed"); }\n    return 0;'),
        ],
        'runtime/cheats.c': [
            ('    rt_log("cheats: %s in %d mods:', '    if (on) { extern void snap_achievements_casual(void); snap_achievements_casual(); }\n    rt_log("cheats: %s in %d mods:'),
            ('    plat_xchg32(&c->on, on != 0);', '    if (on) { extern void snap_achievements_casual(void); snap_achievements_casual(); }\n    plat_xchg32(&c->on, on != 0);'),
        ],
        'runtime/gfx_present.c': [
            ('    prof_write();   // plat_exit runs no atexit handlers', '    { extern void snap_achievements_shutdown(void); snap_achievements_shutdown(); }\n    prof_write();   // plat_exit runs no atexit handlers'),
        ],
    }


def stage_sdk(destination):
    """Preserve SDK sources; independent wrappers avoid static symbol collisions."""
    runtime = Path(destination) / 'runtime'
    vendor = ROOT / 'third_party/recomp_achievements'
    if (vendor / 'VERSION').read_text().strip() != 'faf094acdf1efb57d8db7c8187b4b47aa1501805':
        raise ValueError('Recomp Achievements SDK pin changed')
    target = runtime / 'rlach'
    shutil.copytree(vendor / 'sdk', target / 'sdk', dirs_exist_ok=True)
    shutil.copy2(vendor / 'LICENSE', target / 'LICENSE')
    shutil.copy2(vendor / 'NEWSNAP-NOTICE.md', target / 'NEWSNAP-NOTICE.md')
    sources = [Path('sdk/src/rl_achievements.c'), Path('sdk/third_party/cjson/cJSON.c')]
    for folder in ('runtime', 'util'):
        sources.extend(path.relative_to(vendor) for path in sorted((vendor / 'sdk/third_party/rcheevos/src' / folder).glob('*.c')))
    for source in sources:
        wrapper = runtime / ('snap_rlach_' + source.stem + '.c')
        wrapper.write_text('#define RC_DISABLE_LUA\n#include "rlach/' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    # The existing compiler includes runtime/. Forwarding headers retain every
    # upstream source's relative include hierarchy without changing build flags.
    headers = {}
    for header in (vendor / 'sdk').rglob('*.h'):
        if header.name in headers:
            raise ValueError('Ambiguous SDK header: ' + header.name)
        headers[header.name] = header.relative_to(vendor)
    for name, source in headers.items():
        path = runtime / name
        if path.exists() and not path.read_text(encoding='utf-8').startswith('/* Recomp Achievements forwarder */'):
            raise ValueError('SDK header conflicts with runtime: ' + name)
        path.write_text('/* Recomp Achievements forwarder */\n#include "rlach/' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    (runtime / 'snap_achievements_config.h').write_text(
        '#pragma once\n#define SNAP_ACH_GAME "newsnaprecomp"\n#define SNAP_ACH_VERSION "' + VERSION + '"\n',
        encoding='utf-8', newline='\n')
