"""Resolve owner data beside a release or the developer's verified build."""
from pathlib import Path
import json
import os
import sys
import tempfile


def _selected_data_dir(root):
    root=Path(root)
    try:
        with (root/'launcher-settings.json').open('rb') as stream:
            raw=stream.read(16385)
        if len(raw)>16384:return None
        value=json.loads(raw.decode('utf-8'))
        relative=value.get('game_data_relative')
        if isinstance(relative,str) and relative and not Path(relative).is_absolute():
            candidate=(root/relative).resolve()
            if candidate.is_relative_to(root.resolve()):return candidate
        absolute=value.get('game_data_path')
        if isinstance(absolute,str) and absolute and Path(absolute).is_absolute():return Path(absolute)
    except (OSError,ValueError,TypeError,AttributeError):
        pass
    return None


def select_data_dir(root, selected):
    """Select existing owner inputs without copying, moving or modifying them."""
    root,selected=Path(root).resolve(),Path(selected).resolve()
    candidates=[selected,selected/'GameData',selected/'newsnapGameData']
    selected=next((p for p in candidates if (p/'exefs/main').is_file() and
                   (p/'exefs/sdk').is_file() and (p/'romfs/romfs.bin').is_file()),None)
    if selected is None:
        raise ValueError('Elige una carpeta GameData con ExeFS y RomFS importados de tu juego.')
    path=root/'launcher-settings.json'
    try:
        raw=path.read_bytes()
        value=json.loads(raw.decode('utf-8')) if len(raw)<=16384 else {}
        if not isinstance(value,dict):value={}
    except (OSError,ValueError,TypeError):value={}
    value.pop('game_data_path',None);value.pop('game_data_relative',None)
    value.update({'game_data_relative':selected.relative_to(root).as_posix()} if selected.is_relative_to(root)
                 else {'game_data_path':str(selected)})
    root.mkdir(parents=True,exist_ok=True)
    descriptor,temporary=tempfile.mkstemp(prefix='launcher-settings.',suffix='.tmp',dir=root)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
        os.replace(temporary,path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return selected


def has_game_data(root):
    return _selected_data_dir(root) is not None or any((Path(root) / name / 'newsnap-game.json').is_file() for name in ('GameData', 'newsnapGameData'))


def data_dir(root):
    selected=_selected_data_dir(root)
    if selected is not None:return selected
    for name in ('GameData', 'newsnapGameData'):
        directory = Path(root) / name
        if (directory / 'newsnap-game.json').is_file():
            return directory
    return Path(root) / 'GameData'


def is_release_layout(root):
    return bool(getattr(sys, 'frozen', False)) or has_game_data(root)


def runtime_dir(root):
    return data_dir(root) if is_release_layout(root) else Path(root) / 'build/updated'


def default_profile(root):
    return data_dir(root) / 'profile' if is_release_layout(root) else Path(root) / 'build/profile'


def shader_library_dir(root):
    return data_dir(root) / 'shader-libraries' if is_release_layout(root) else Path(root) / 'build/shader-unpack/programs'


def module_path(root):
    return data_dir(root) / 'exefs/main' if is_release_layout(root) else Path(root) / 'build/extracted/updated/exefs/main'
