"""Load the pinned infrastructure without modifying its working tree."""
import functools
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / 'third_party' / 'astral'
COMMIT = '248e0b29f308ca84a2d2092019cc60e7fc50ae85'
TITLE_ID = '0100F4300BF2C000'
UPDATE_ID = '0100F4300BF2C800'


@functools.lru_cache
def extractor():
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
    module.program_nca = select_program
    return module
