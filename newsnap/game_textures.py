"""HD shadows mode for every level, from the player's own game files (HD-SHADOW-02).

The baked shadows of a level are textures of its archive (nx/Pack/LevelComposite/master/LC_*.drp), two per mesh:

    <level>^<model>^<id>^<shape>^<n>^0^Lightmap.nutexb   the light of the mesh (BC6H, 64 to 512 texels). Maps ^1^,
                                                         ^2^ and ^3^ hold directional terms and are left alone.
    <level>^<model>^<id>^<shape>^<n>^Shadow.nutexb       the sun shadows painted on the mesh (BC3, the shadow in
                                                         alpha, 64 to 2048 texels)

Those two name rules are the list of textures this mode replaces. For each level archive, the members not built yet
are handed to the game's own decoder (newsnap.exe with a request file, as newsnap/unpack.py does for shaders;
newsnap/overlays/snap_decode.c kinds 1 and 2), which writes them to <GameData>/hdshadows/src as pictures named by the
hash the runtime gives the texture at load time. newsnap/hdshadows.py enlarges them into <GameData>/hdshadows, and
the pictures of src are removed. When every archive is done, <GameData>/hdshadows/all-maps is written: the runtime
then shows HD shadows on the first visit to any level and saves nothing while playing.

What is already built is recognised without reading the game image again. all-maps records the image it was built
from (image_key): a start with everything built returns at once. state.json records, for that same image, each
level archive whose shadows are all built (and the archives that hold none), so a build that was stopped goes on
reading only the archives that are left. Another game image, or a new BUILD, starts the reading again.

    python -m newsnap.game_textures --runtime <GameData> [--data <GameData>] [--only LC_001_A] [--limit N]

Everything is made on the player's PC from the player's files; nothing here is distributed.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from .drp import entries, payload

TEXTURE = '5c156dbc'          # extension CRC of .nutexb members
LIGHT, SHADOW = 1, 2          # request kinds (snap_decode.c)
RULES = ((re.compile(r'\^\d+\^0\^Lightmap\.nutexb$'), LIGHT), (re.compile(r'\^\d+\^Shadow\.nutexb$'), SHADOW))
BUILD = 1                     # raise when the pictures made from the same game files change
MARKER, STATE = 'all-maps', 'state.json'
REQUEST_BYTES = 256 << 20     # stored bytes per request file
REQUEST_MEMBERS = 400         # members per request: progress every few hundred textures, little kept in src


def romfs_files(index):
    """(path, offset, size) of every file of the game image, from the runtime's romfs-index.bin (ACRFS1)."""
    data = Path(index).read_bytes()
    if len(data) < 24 or data[:6] != b'ACRFS1':
        raise ValueError('romfs-index.bin no tiene el formato esperado')
    count, strings = struct.unpack_from('<QQ', data, 8)
    if 24 + 24 * count > len(data) or strings > len(data):
        raise ValueError('romfs-index.bin está incompleto')
    out = []
    for i in range(count):
        offset, size, name, length = struct.unpack_from('<QQII', data, 24 + 24 * i)
        if strings + name + length > len(data) or not length:
            raise ValueError('romfs-index.bin está incompleto')
        out.append((data[strings + name:strings + name + length - 1].decode('utf-8'), offset, size))
    return out


def kind_of(name):
    for rule, kind in RULES:
        if rule.search(name):
            return kind
    return 0


def level_archive(path):
    return path.endswith('.drp') and '/LevelComposite/' in path


def archive_members(image, offset, size):
    """[member entry + 'kind'] of the baked shadows of one level archive (reads the index of the archive)."""
    found = []
    for item in entries(image, offset, size):
        kind = kind_of(item['name']) if item['extension_crc'] == TEXTURE else 0
        if kind and item['decompressed_size'] <= 64 << 20 and item['compressed_size'] <= 64 << 20:
            found.append(dict(item, kind=kind, archive_offset=offset))
    return found


def shadow_members(image, files):
    """{archive path: [member entry + 'kind']} for the archives that hold baked shadows, in path order."""
    out = {}
    for path, offset, size in files:
        if not level_archive(path):
            continue
        found = archive_members(image, offset, size)
        if found:
            out[path] = found
    return out


def image_key(runtime, data=None):
    """The game image the shadows are built from: the digest of the runtime's index of it (200 KB) and its size."""
    runtime = Path(runtime)
    data = Path(data) if data else runtime
    index = hashlib.sha256((runtime / 'romfs-index.bin').read_bytes()).hexdigest()
    return f'{index}:{(data / "romfs/romfs.bin").stat().st_size}'


def write_request(image, members, path):
    """Request version 2 (snap_decode.c): header, then per member six words and its stored bytes."""
    with open(path, 'wb') as stream:
        stream.write(struct.pack('<3I', 0x444F534E, 2, len(members)))
        for ordinal, item in enumerate(members):
            stored = payload(image, item['archive_offset'], item)
            stream.write(struct.pack('<6I', ordinal, len(stored), item['decompressed_size'], item['crc32'],
                                     int(item['compressed']), item['kind']))
            stream.write(stored)


class Stopped(Exception):
    """The player stopped the build, or the launcher needs the runtime (a game start, an update)."""


def run_export(runtime, data, request, out, work, cancel=None):
    """The game's decoder on one request; returns {ordinal: (result, hash)} from <out>/export.txt."""
    runtime, data = Path(runtime), Path(data)
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('AC_', 'NEWSNAP_'))}
    env.update(AC_GPU='null', NEWSNAP_OODLE_REQUESTS=str(request), NEWSNAP_OODLE_OUTPUT=str(out),
               AC_ROMFS_INDEX=str(runtime / 'romfs-index.bin'))
    listing = Path(out) / 'export.txt'
    listing.unlink(missing_ok=True)
    command = [str(runtime / 'newsnap.exe'), '--exefs', str(data / 'exefs'), '--romfs', str(data / 'romfs'),
               '--profile', str(Path(work) / 'profile'), '--boot']
    with open(Path(work) / 'export.log', 'wb') as log:
        done = subprocess.Popen(command, cwd=runtime, env=env, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        waited = 0.0
        while True:
            try:
                done.wait(0.25)
                break
            except subprocess.TimeoutExpired:
                waited += 0.25
                if (cancel is not None and cancel.is_set()) or waited > 1800:
                    done.kill()
                    done.wait()
                    if waited > 1800:
                        raise ValueError('el juego tardó demasiado en leer sus texturas')
                    raise Stopped()
    if done.returncode or not listing.is_file():
        tail = (Path(work) / 'export.log').read_bytes()[-400:].decode('utf-8', 'replace').strip().splitlines()
        raise ValueError('el juego no pudo leer sus texturas' + (f' ({tail[-1]})' if tail else ''))
    results = {}
    for line in listing.read_text(encoding='ascii').split('\n'):
        parts = line.split()
        if len(parts) == 3:
            results[int(parts[0])] = (int(parts[1]), parts[2])
    listing.unlink(missing_ok=True)
    return results


def _state(folder, image=None):
    """state.json of this BUILD. 'hashes': member checksum -> texture hash ('-': not used). 'archives': archive
    path -> number of shadow members, for the archives of the game image 'image' that need no more reading."""
    state = {'build': BUILD, 'hashes': {}}
    try:
        value = json.loads((Path(folder) / STATE).read_text(encoding='utf-8'))
        if isinstance(value, dict) and value.get('build') == BUILD and isinstance(value.get('hashes'), dict):
            state = value
    except (OSError, ValueError):
        pass
    archives = state.get('archives')
    if (image is None or state.get('image') != image or not isinstance(archives, dict)
            or not all(isinstance(k, str) and type(v) is int and v >= 0 for k, v in archives.items())):
        state['archives'] = {}
    state['image'] = image
    return state


def _save_state(folder, state):
    tmp = Path(folder) / (STATE + '.part')
    tmp.write_text(json.dumps(state, separators=(',', ':')), encoding='utf-8')
    tmp.replace(Path(folder) / STATE)


def _built(folder, name):
    """name: the texture's hash, '-' for a member this mode does not use, '' for one not read yet."""
    return name == '-' or bool(name) and ((folder / f'{name}.dds').is_file() or (folder / f'{name}.skip').is_file())


def _built_names(folder):
    """The texture hashes that have an HD file or a skip in folder, from one directory listing."""
    try:
        with os.scandir(folder) as found:
            return {entry.name.rsplit('.', 1)[0] for entry in found if entry.name.endswith(('.dds', '.skip'))}
    except OSError:
        return set()


def complete(folder, image=None):
    """True when the HD shadows of every level were built from the game files by this version.

    image (image_key): also that they were built from that game image. Markers written before the image was
    recorded have none: they still count without image, and install() reads the levels once to add it.
    """
    try:
        marker = json.loads((Path(folder) / MARKER).read_text(encoding='utf-8'))
        return marker.get('build') == BUILD and (image is None or marker.get('image') == image)
    except (OSError, ValueError, AttributeError):
        return False


def install(runtime, data=None, report=print, cancel=None, only=None, limit=0, scale=2):
    """Build the HD shadows of every level into <runtime>/hdshadows. Returns (made, left as they are, failed).

    It can be stopped (cancel, a threading.Event) and started again: what is built stays.
    """
    from . import hdshadows
    runtime = Path(runtime)
    data = Path(data) if data else runtime
    folder = runtime / 'hdshadows'
    image_id = image_key(runtime, data)
    if not only and not limit and complete(folder, image_id):
        return (0, 0, 0)   # everything is built from this game image: nothing to read
    src = folder / 'src'
    src.mkdir(parents=True, exist_ok=True)
    state = _state(folder, image_id)
    hashes, recorded = state['hashes'], state['archives']
    present = _built_names(folder)
    built = lambda name: name == '-' or bool(name) and name in present
    if recorded and not all(built(name) for name in hashes.values()):
        recorded.clear()   # HD files were removed by hand: every archive is read again
    stopped = lambda: cancel is not None and cancel.is_set()
    totals = [0, 0, 0]
    report('Sombras HD: leyendo los niveles del juego…')
    with open(data / 'romfs/romfs.bin', 'rb') as image, tempfile.TemporaryDirectory(prefix='hdshadows-') as work:
        levels = [entry for entry in romfs_files(runtime / 'romfs-index.bin') if level_archive(entry[0])]
        whole, todo, noted = 0, {}, False
        for path, offset, size in levels:
            if only and only not in path:
                continue
            if path in recorded:   # all built in an earlier run, or no shadows in it: not read again
                whole += recorded[path]
                continue
            items = archive_members(image, offset, size)
            whole += len(items)
            left = [m for m in items if not built(hashes.get(f'{m["crc32"]:08x}', ''))]
            if left:
                todo[path] = (len(items), left)
            else:
                recorded[path] = len(items)
                noted = True
        if not whole:
            raise ValueError('no se encontraron los niveles en los archivos del juego')
        if noted:
            _save_state(folder, state)
        start = whole - sum(len(left) for _, left in todo.values())
        done = 0
        for path, (count, members) in todo.items():
            level = Path(path).stem
            checks = [f'{m["crc32"]:08x}' for m in members]
            while members and not stopped() and (not limit or done < limit):
                report(f'Sombras HD: {start + done} de {whole} texturas · leyendo el nivel {level}…')
                batch, size = [], 0
                while members and len(batch) < REQUEST_MEMBERS and size < REQUEST_BYTES and \
                        (not limit or done + len(batch) < limit):
                    batch.append(members.pop(0))
                    size += batch[-1]['compressed_size']
                request = Path(work) / 'request.bin'
                write_request(image, batch, request)
                try:
                    results = run_export(runtime, data, request, src, work, cancel)
                except Stopped:
                    break
                finally:
                    request.unlink(missing_ok=True)
                names = []
                for ordinal, item in enumerate(batch):
                    result, name = results.get(ordinal, (-1, ''))
                    if result == 1:
                        hashes[f'{item["crc32"]:08x}'] = name
                        names.append(name)
                    else:   # not a texture this mode uses (another format or size): never asked again
                        hashes[f'{item["crc32"]:08x}'] = '-'
                _save_state(folder, state)
                base = start + done

                def progress(n, _total, base=base, level=level):
                    report(f'Sombras HD: {base + n} de {whole} texturas · nivel {level}')

                sources = [p for name in dict.fromkeys(names) for p in (src / f'{name}.dds', src / f'{name}.png')
                           if p.is_file()]
                made, kept, failed = hdshadows.generate(folder, scale, sources=sources, progress=progress,
                                                        report=report, cancel=cancel)
                totals[0] += made
                totals[1] += kept
                totals[2] += failed
                for source in sources:   # the pictures of src are only needed to build
                    if _built(folder, source.stem):
                        source.unlink(missing_ok=True)
                done += len(batch)
            if not members and all(_built(folder, hashes.get(check, '')) for check in checks):
                recorded[path] = count   # every shadow of this archive is built: it is not read again
                _save_state(folder, state)
        finished = not stopped() and not limit and not only and not totals[2] and \
            all(path in recorded for path, _, _ in levels)
    if finished:
        (folder / MARKER).write_text(json.dumps({'build': BUILD, 'textures': whole, 'image': image_id}),
                                     encoding='utf-8')
        shutil.rmtree(src, ignore_errors=True)
    return tuple(totals)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runtime', type=Path, required=True, help='folder of newsnap.exe and romfs-index.bin')
    ap.add_argument('--data', type=Path, help='folder of exefs and romfs (default: the runtime folder)')
    ap.add_argument('--only', help='only the archives whose path contains this text')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args(argv)
    from .hdshadows import ensure_esrgan
    ensure_esrgan()
    made, kept, failed = install(a.runtime, a.data, report=lambda text: print(text, flush=True), only=a.only,
                                 limit=a.limit)
    print(f'{made} HD shadow textures written, {kept} left as they are, {failed} failed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
