"""Resolve owner data beside a release or the developer's verified build."""
from pathlib import Path
import sys


def has_game_data(root):
    return any((Path(root) / name / 'newsnap-game.json').is_file() for name in ('GameData', 'newsnapGameData'))


def data_dir(root):
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
