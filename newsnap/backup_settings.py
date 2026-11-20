"""Explicit full-profile backup opt-in; no cloud provider or UI dependency."""
import json
import os
from pathlib import Path
import tempfile

from . import launcher_settings as settings
from .paths import runtime_dir
from .profile_backup import _no_links


def settings_path(root):
    return runtime_dir(root) / 'backup-settings.json'


def _validate(value):
    if (not isinstance(value, dict) or type(value.get('format')) is not int or value['format'] != 1
            or not isinstance(value.get('destination'), str) or not value['destination']
            or not Path(value['destination']).is_absolute()
            or type(value.get('keep')) is not int or not 1 <= value['keep'] <= 100):
        raise ValueError('Invalid full-profile backup settings')
    return {'format': 1, 'destination': str(Path(os.path.abspath(value['destination']))), 'keep': value['keep']}


def load_backup_settings(root):
    """Return validated opt-in, None when disabled; malformed settings raise."""
    path = settings_path(root)
    _no_links(path)
    try:
        with path.open('rb') as stream:
            raw = stream.read(8193)
    except FileNotFoundError:
        return None
    if len(raw) > 8192:
        raise ValueError('Full-profile backup settings exceed the size limit')
    return _validate(json.loads(raw))


def validate_destination(destination, profile, *, probe=False):
    """Reject profile descendants and links, optionally probe real folder writes."""
    destination, profile = Path(os.path.abspath(destination)), Path(os.path.abspath(profile))
    _no_links(destination)
    _no_links(profile)
    if destination == profile or profile in destination.parents:
        raise ValueError('Choose a backup folder outside the current profile')
    if not destination.is_dir():
        raise ValueError('Choose an existing backup folder')
    if probe:
        fd, name = tempfile.mkstemp(prefix='.newsnap-backup-probe-', dir=destination)
        try:
            os.close(fd)
        finally:
            Path(name).unlink()
    return destination


def save_backup_settings(root, destination, keep=3, *, profile=None):
    """Persist only after the caller has obtained explicit user consent."""
    if not Path(destination).is_absolute():
        raise ValueError('Backup folder must be an absolute path')
    config = _validate({'format': 1, 'destination': str(destination), 'keep': keep})
    validate_destination(config['destination'], settings.load_profile(root) if profile is None else profile,
                         probe=True)
    path = settings_path(root)
    _no_links(path)
    settings._atomic_write(path, (json.dumps(config) + '\n').encode('utf-8'))
    return config


def disable_backup_settings(root):
    """Disable future backups; never remove any backup archive."""
    path = settings_path(root)
    _no_links(path)
    path.unlink(missing_ok=True)


def backup_after_session(root, profile, report=print):
    """Back up when opted in. Caller MUST still hold ProfileLock(profile).

    A backup or settings failure is a warning and never replaces the game's exit
    status. This function performs no provider login, upload or UI operation.
    """
    try:
        config = load_backup_settings(root)
        if config is None:
            return None
        destination = validate_destination(config['destination'], profile)
        from .profile_backup import backup_profile
        return backup_profile(profile, destination, keep=config['keep'], report=report)
    except Exception as error:
        try:
            report(f'Full-profile backup warning: {error}')
        except Exception:
            pass  # Reporting must not mask the game's final result either.
        return None
