"""Load the pinned infrastructure without modifying its working tree."""
import functools
import importlib.util
import sys
from pathlib import Path

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / 'third_party' / 'astral'
COMMIT = '248e0b29f308ca84a2d2092019cc60e7fc50ae85'
TITLE_ID = '0100F4300BF2C000'
UPDATE_ID = '0100F4300BF2C800'


@functools.lru_cache
def extractor(content_type=0):
    path = UPSTREAM / 'tools' / 'extract.py'
    if not path.is_file():
        raise ValueError('Initialize the upstream with git submodule update --init')
    spec = importlib.util.spec_from_file_location('newsnap_nca_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.GAME_TITLE_ID = TITLE_ID
    module.UPDATE_TITLE_ID = UPDATE_ID
    # The reader is shared, but title identity and program selection belong to Snap.
    from .importer import select_program
    if content_type == 0:
        module.program_nca = select_program
    elif content_type == 2:
        def select_control(records, update=False):
            controls = [(r, h) for r, h in records if r['content_type'] == 2 and r['title_id'] == TITLE_ID]
            if len(controls) != 1:
                raise ValueError('Expected one New Pokémon Snap Control NCA')
            return controls[0]
        module.program_nca = select_control
    else:
        raise ValueError('Unsupported NCA content selection')
    return module
