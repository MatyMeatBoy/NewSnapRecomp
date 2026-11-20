"""Run a verified writable public installation with the original entry arguments."""
import json
import os
from pathlib import Path
import subprocess

from .install_location import writable_install


def _absolute_inputs(root, arguments):
    paths={'--game','--update','--keys','--apply-update'}
    result=[];next_path=False
    for argument in arguments:
        if next_path:
            result.append(str(Path(os.path.abspath(root/argument))));next_path=False;continue
        key,separator,value=argument.partition('=')
        if key in paths:
            if separator: result.append(key+'='+str(Path(os.path.abspath(root/value))))
            else: result.append(key);next_path=True
        else: result.append(argument)
    return result


def relocate_if_needed(root, arguments):
    root = Path(root).absolute()
    target = writable_install(root)
    if target == root:
        return None
    env = dict(os.environ, NEWSNAP_READONLY_SOURCE=str(root))
    # Remember only the harmless language choice. Owner game/profile data is
    # selected and, if necessary, copied with a visible separate consent flow.
    language, selected = root/'launcher-language.json', target/'launcher-language.json'
    try:
        if language.is_file() and not language.is_symlink() and not selected.exists():
            with language.open('rb') as stream: data=stream.read(8193)
            if len(data) <= 8192 and isinstance(json.loads(data), dict):
                from .launcher_settings import _atomic_write
                _atomic_write(selected,data)
    except (OSError, ValueError, UnicodeError):
        pass  # Invalid optional preferences must not prevent a safe relocation.
    from .paths import has_game_data, data_dir
    if not has_game_data(target) and has_game_data(root):
        env['NEWSNAP_PENDING_DATA'] = str(data_dir(root))
    result = subprocess.run([str(target/'NewSnapLauncher.exe'),*_absolute_inputs(root,arguments)],cwd=target,
                            env=env,close_fds=False)
    return result.returncode
