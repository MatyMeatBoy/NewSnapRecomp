"""«Añadir a Steam» and «Acceso directo» for the launcher, the way ReKHCoM's launcher does them (decompui.cpp).

Steam keeps non-Steam games in userdata/<account>/config/shortcuts.vdf (binary KeyValues: 0x00 a map, 0x01 a string,
0x02 an int32, 0x07 a uint64, 0x08 the end of a map; names and strings end with a zero). The entry starts
NewSnapLauncher.exe --play, which opens the game straight away with the saved settings. Its artwork goes to the
account's config/grid as <appid>p.jpg (library cover), <appid>.jpg (wide capsule), <appid>_hero.jpg and
<appid>_logo.png, made from the launcher's own images. A file that cannot be read is never overwritten; a backup
(shortcuts.vdf.newsnap-backup) is kept before every write. Steam reads the list when it starts.
"""
import os
from pathlib import Path
import shutil
import subprocess
import zlib

NAME = 'NewSnap · New Pokémon Snap'
BACKUP = 'shortcuts.vdf.newsnap-backup'


# ---- binary KeyValues ----------------------------------------------------------------------------------------------

def vdf_read(data, at=0):
    """(items, next offset): items is a list of [key, type, value] (a map's value is its own items)."""
    items = []
    while at < len(data):
        kind = data[at]
        at += 1
        if kind == 0x08:
            return items, at
        end = data.index(b'\0', at)
        key = data[at:end].decode('utf-8', 'replace')
        at = end + 1
        if kind == 0x00:
            value, at = vdf_read(data, at)
        elif kind == 0x01:
            end = data.index(b'\0', at)
            value = data[at:end].decode('utf-8', 'replace')
            at = end + 1
        elif kind in (0x02, 0x07):
            size = 4 if kind == 0x02 else 8
            if at + size > len(data):
                raise ValueError('truncated shortcuts.vdf')
            value = int.from_bytes(data[at:at + size], 'little')
            at += size
        else:
            raise ValueError(f'unknown KeyValues type {kind}')
        items.append([key, kind, value])
    raise ValueError('shortcuts.vdf ends inside a map')


def vdf_write(items):
    out = bytearray()
    for key, kind, value in items:
        out += bytes([kind]) + key.encode('utf-8') + b'\0'
        if kind == 0x00:
            out += vdf_write(value)
        elif kind == 0x01:
            out += value.encode('utf-8') + b'\0'
        else:
            out += int(value).to_bytes(4 if kind == 0x02 else 8, 'little')
    return bytes(out + b'\x08')


def _find(items, key):
    for item in items:
        if item[0].lower() == key.lower():
            return item
    return None


def _set(items, key, kind, value):
    item = _find(items, key)
    if item is None:
        items.append([key, kind, value])
    else:
        item[1], item[2] = kind, value


# ---- Steam folders -------------------------------------------------------------------------------------------------

def steam_folder():
    override = os.environ.get('NEWSNAP_STEAM_DIR')   # tests: a copy of Steam's folders
    if override:
        return Path(override)
    if os.name != 'nt':
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
            return Path(winreg.QueryValueEx(key, 'SteamPath')[0])
    except OSError:
        return None


def user_configs(steam):
    """The account that signed in last (loginusers.vdf: MostRecent, else the newest timestamp), else every account."""
    if steam is None:
        return []
    best, newest, most_recent, current = None, -1, False, None
    try:
        lines = (steam / 'config' / 'loginusers.vdf').read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        lines = []
    for line in lines:
        parts = line.split('"')
        if len(parts) == 3 and len(parts[1]) == 17 and parts[1].isdigit():
            current = parts[1]
        elif current and len(parts) >= 5 and not most_recent:
            key, value = parts[1], parts[3]
            if key == 'MostRecent' and value == '1':
                best, most_recent = current, True
            elif key == 'timestamp' and value.isdigit() and int(value) >= newest:
                newest, best = int(value), current
    if best:
        folder = steam / 'userdata' / str(int(best) & 0xFFFFFFFF) / 'config'
        if folder.is_dir():
            return [folder]
    userdata = steam / 'userdata'
    return [p / 'config' for p in sorted(userdata.iterdir()) if p.name != '0' and (p / 'config').is_dir()] \
        if userdata.is_dir() else []


def _quoted(path):
    return f'"{Path(path)}"'


def _ours(entry, root):
    exe = _find(entry, 'Exe')
    folder = _find(entry, 'StartDir')
    root = str(Path(root)).lower()
    return bool((exe and root in str(exe[2]).lower()) or (folder and str(folder[2]).lower().strip('"') == root))


def _read(path):
    if not path.is_file():
        return []
    items, _ = vdf_read(path.read_bytes())
    return items


def in_steam(root):
    for config in user_configs(steam_folder()):
        try:
            shortcuts = _find(_read(config / 'shortcuts.vdf'), 'shortcuts')
        except (OSError, ValueError):
            continue
        if shortcuts and any(entry[1] == 0x00 and _ours(entry[2], root) for entry in shortcuts[2]):
            return True
    return False


def _artwork(grid, appid, assets):
    from PIL import Image
    grid.mkdir(parents=True, exist_ok=True)

    def fill(src, size, out):
        with Image.open(src) as im:
            im = im.convert('RGB')
            scale = max(size[0] / im.width, size[1] / im.height)
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
            left, top = (im.width - size[0]) // 2, (im.height - size[1]) // 2
            im.crop((left, top, left + size[0], top + size[1])).save(out, quality=92)

    fill(assets / 'lental-hero.jpg', (600, 900), grid / f'{appid}p.jpg')
    fill(assets / 'lental-explore.jpg', (920, 430), grid / f'{appid}.jpg')
    fill(assets / 'lental-explore.jpg', (1920, 620), grid / f'{appid}_hero.jpg')
    shutil.copyfile(assets / 'snap-logo.png', grid / f'{appid}_logo.png')


def add_to_steam(root, launcher_exe, assets):
    """Adds or updates the entry for this installation. Returns how many Steam accounts were updated."""
    root, launcher_exe = Path(root), Path(launcher_exe)
    exe, start = _quoted(launcher_exe), _quoted(root)
    appid = (zlib.crc32((exe + NAME).encode('utf-8')) | 0x80000000) & 0xFFFFFFFF
    done = 0
    for config in user_configs(steam_folder()):
        path = config / 'shortcuts.vdf'
        try:
            items = _read(path)
        except (OSError, ValueError):
            continue   # not understood: never overwritten
        shortcuts = _find(items, 'shortcuts')
        if shortcuts is None:
            shortcuts = ['shortcuts', 0x00, []]
            items.append(shortcuts)
        entry = next((e[2] for e in shortcuts[2] if e[1] == 0x00 and _ours(e[2], root)), None)
        if entry is None:
            entry = []
            shortcuts[2].append([str(len(shortcuts[2])), 0x00, entry])
        _set(entry, 'appid', 0x02, appid)
        _set(entry, 'AppName', 0x01, NAME)
        _set(entry, 'Exe', 0x01, exe)
        _set(entry, 'StartDir', 0x01, start)
        _set(entry, 'icon', 0x01, str(launcher_exe))
        _set(entry, 'LaunchOptions', 0x01, '--play')
        _set(entry, 'AllowOverlay', 0x02, 1)
        _set(entry, 'AllowDesktopConfig', 0x02, 1)
        if _find(entry, 'tags') is None:
            entry.append(['tags', 0x00, []])
        data = vdf_write(items)
        if path.is_file():
            shutil.copyfile(path, config / BACKUP)
        temporary = path.with_suffix('.vdf.part')
        temporary.write_bytes(data)
        temporary.replace(path)
        _artwork(config / 'grid', appid, Path(assets))
        done += 1
    return done


def remove_from_steam(root):
    removed = 0
    for config in user_configs(steam_folder()):
        path = config / 'shortcuts.vdf'
        try:
            items = _read(path)
        except (OSError, ValueError):
            continue
        shortcuts = _find(items, 'shortcuts')
        if not shortcuts:
            continue
        keep, gone = [], []
        for entry in shortcuts[2]:
            if entry[1] == 0x00 and _ours(entry[2], root):
                appid = _find(entry[2], 'appid')
                if appid:
                    gone.append(appid[2])
            else:
                keep.append(entry)
        if not gone:
            continue
        for index, entry in enumerate(keep):   # Steam numbers them 0, 1, 2 ...
            entry[0] = str(index)
        shortcuts[2] = keep
        shutil.copyfile(path, config / BACKUP)
        path.write_bytes(vdf_write(items))
        for appid in gone:
            for suffix in ('p.jpg', 'p.png', '.jpg', '.png', '_hero.jpg', '_hero.png', '_logo.png'):
                (config / 'grid' / f'{appid}{suffix}').unlink(missing_ok=True)
        removed += 1
    return removed


# ---- desktop shortcut ----------------------------------------------------------------------------------------------

def desktop_shortcut(root, launcher_exe, play=True):
    """A NewSnap.lnk on the desktop that opens the game (--play) or the launcher. Returns its path."""
    if os.name != 'nt':
        raise OSError('Los accesos directos solo se crean en Windows')
    import ctypes
    from ctypes import wintypes
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)   # CSIDL_DESKTOPDIRECTORY
    desktop = Path(os.environ.get('NEWSNAP_DESKTOP_DIR') or buf.value)
    link = desktop / ('New Pokémon Snap (NewSnap).lnk' if play else 'NewSnap Launcher.lnk')
    script = ('$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:NS_LINK);'
              '$s.TargetPath=$env:NS_EXE;$s.Arguments=$env:NS_ARGS;$s.WorkingDirectory=$env:NS_DIR;'
              '$s.IconLocation=$env:NS_EXE+",0";$s.Description="New Pokemon Snap (NewSnap)";$s.Save()')
    env = dict(os.environ, NS_LINK=str(link), NS_EXE=str(launcher_exe), NS_ARGS='--play' if play else '',
               NS_DIR=str(root))
    subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], env=env, check=True,
                   capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=60)
    if not link.is_file():
        raise OSError('No se pudo crear el acceso directo')
    return link
