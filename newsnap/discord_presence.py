"""Discord Rich Presence for the launcher: "playing New Pokémon Snap" while the game is open.

Discord's desktop client listens on a local named pipe (\\\\.\\pipe\\discord-ipc-0 to -9). A client says which
application it is (the application id of a Discord developer application, which gives the name and pictures Discord
shows) and then sets an activity: two lines of text and a start time. Nothing is sent over the network by this module
and no Discord library is used; when Discord is not running, or no application id is set, nothing happens.

The only data sent is the text built here (the game's name, a fixed state line) and the launcher's process id, which
Discord uses to clear the activity when the process ends. No profile, photo, path or account data.

Settings live in launcher-settings.json beside the launcher: `discord_presence` (true by default) and, to use another
Discord application, `discord_app_id`.
"""
import json
import os
import struct
import tempfile
import threading
import time
import uuid
from pathlib import Path

# The Discord application whose name and pictures are shown (the owner's, 2026-11-15); launcher-settings.json
# (`discord_app_id`) can name another. An application id is public: it only says which application's name to show.
APPLICATION_ID = '1571711879179403366'
DETAILS = 'New Pokémon Snap'
STATE = 'En una expedición'
LARGE_IMAGE, LARGE_TEXT = 'newsnap', 'NewSnap · port nativo para PC'
HANDSHAKE, FRAME, CLOSE = 0, 1, 2


def _settings(root):
    try:
        raw = (Path(root) / 'launcher-settings.json').read_bytes()
        value = json.loads(raw.decode('utf-8')) if len(raw) <= 16384 else {}
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def enabled(root):
    return _settings(root).get('discord_presence', True) is not False


def application_id(root):
    value = _settings(root).get('discord_app_id') or APPLICATION_ID
    value = str(value).strip()
    return value if value.isdigit() and 15 <= len(value) <= 24 else ''


def set_enabled(root, on):
    """Keep the choice in launcher-settings.json without touching its other keys."""
    root = Path(root)
    value = _settings(root)
    value['discord_presence'] = bool(on)
    root.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='launcher-settings.', suffix='.tmp', dir=root)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, root / 'launcher-settings.json')
    finally:
        Path(temporary).unlink(missing_ok=True)


def frame(opcode, payload):
    data = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return struct.pack('<II', opcode, len(data)) + data


def activity(started, pid, details=DETAILS, state=STATE):
    """The SET_ACTIVITY command; started None clears the activity."""
    shown = None if started is None else {
        'details': details, 'state': state, 'timestamps': {'start': int(started)},
        'assets': {'large_image': LARGE_IMAGE, 'large_text': LARGE_TEXT}}
    return {'cmd': 'SET_ACTIVITY', 'args': {'pid': pid, 'activity': shown}, 'nonce': uuid.uuid4().hex}


def _open_pipe():
    for n in range(10):
        try:
            return open(rf'\\.\pipe\discord-ipc-{n}', 'r+b', buffering=0)
        except OSError:
            continue
    return None


def _read(pipe):
    header = pipe.read(8)
    if len(header) != 8:
        raise OSError('Discord closed the pipe')
    opcode, length = struct.unpack('<II', header)
    if length > 1 << 20:
        raise OSError('Discord sent an oversized frame')
    body = pipe.read(length) if length else b''
    return opcode, json.loads(body.decode('utf-8')) if body else {}


class Presence:
    """start() when the game opens, stop() when it ends. Every failure is silent: the game is never affected."""

    def __init__(self, root, opener=_open_pipe, pid=None):
        self.root, self.opener, self.pid = Path(root), opener, pid or os.getpid()
        self.pipe, self.lock = None, threading.Lock()

    def start(self, started=None):
        app = application_id(self.root)
        if not app or not enabled(self.root):
            return False
        threading.Thread(target=self._start, args=(app, started or time.time()), daemon=True).start()
        return True

    def _start(self, app, started):
        with self.lock:
            try:
                self._close()
                pipe = self.opener()
                if pipe is None:
                    return False
                self.pipe = pipe
                pipe.write(frame(HANDSHAKE, {'v': 1, 'client_id': app}))
                opcode, answer = _read(pipe)
                if opcode != FRAME or answer.get('evt') != 'READY':
                    self._close()
                    return False
                pipe.write(frame(FRAME, activity(started, self.pid)))
                _read(pipe)
                return True
            except (OSError, ValueError):
                self._close()
                return False

    def stop(self):
        threading.Thread(target=self._stop, daemon=True).start()

    def _stop(self):
        with self.lock:
            if self.pipe is None:
                return
            try:
                self.pipe.write(frame(FRAME, activity(None, self.pid)))
                _read(self.pipe)
            except (OSError, ValueError):
                pass
            self._close()

    def _close(self):
        pipe, self.pipe = self.pipe, None
        if pipe is not None:
            try:
                pipe.close()
            except OSError:
                pass
