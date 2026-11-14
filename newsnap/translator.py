"""Verify the exact public NativeAOT translator; recipe id alone is not trust."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from .upstream import ROOT

PIN = ROOT / 'profiles/translator-windows.json'
_HEX = re.compile(r'[0-9a-f]{64}')


def verify_translator(directory, *, pin_path=None):
    """Check binary and id independently, without executing an untrusted tool."""
    try:
        pin = json.loads(Path(pin_path or PIN).read_text(encoding='utf-8'))
        if (pin.get('format') != 1 or pin.get('platform') != 'windows-x64' or
                type(pin.get('size')) is not int or not 0 < pin['size'] <= (64 << 20) or
                not isinstance(pin.get('sha256'), str) or not _HEX.fullmatch(pin['sha256']) or
                not isinstance(pin.get('identity'), str) or not _HEX.fullmatch(pin['identity'])):
            raise ValueError('invalid public pin')
        directory = Path(directory)
        executable, identity = directory / 'ac_xlate.exe', directory / 'ac_xlate.id'
        for path in (executable, identity):
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()) or not path.is_file():
                raise ValueError('missing or linked tool file')
        if executable.stat().st_size != pin['size'] or identity.stat().st_size > 66:
            raise ValueError('tool size differs from public pin')
        expected_id = pin['identity'].encode('ascii')
        if identity.read_bytes() not in (expected_id, expected_id + b'\n', expected_id + b'\r\n'):
            raise ValueError('recipe identity differs from public pin')
        hasher = hashlib.sha256()
        with executable.open('rb') as stream:
            remaining = pin['size']
            while remaining:
                chunk = stream.read(min(1 << 20, remaining))
                if not chunk:
                    raise ValueError('executable changed during verification')
                hasher.update(chunk)
                remaining -= len(chunk)
            if stream.read(1):
                raise ValueError('executable grew during verification')
        if hasher.hexdigest() != pin['sha256']:
            raise ValueError('executable differs from public pin')
        return pin
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ValueError(f'Unverified shader translator: {error}') from error


def stage_translator(source, destination, *, pin_path=None):
    """Validate both sides of a bounded copy before publishing either file."""
    verify_translator(source, pin_path=pin_path)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.translator-', dir=destination) as temporary:
        staged = Path(temporary)
        for name in ('ac_xlate.exe', 'ac_xlate.id'):
            shutil.copy2(Path(source) / name, staged / name)
        verify_translator(staged, pin_path=pin_path)
        for name in ('ac_xlate.exe', 'ac_xlate.id'):
            (staged / name).replace(destination / name)
    verify_translator(destination, pin_path=pin_path)
