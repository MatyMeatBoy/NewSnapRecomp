"""Launcher-only language: Windows display language, with a remembered user choice."""
import ctypes
import json
import locale
import os
from pathlib import Path
import tempfile

from .launcher_strings import ENGLISH

_language = 'es'


def windows_ui_language():
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lang_id, 'en-US')
    except (AttributeError, OSError):
        return None


def system_language():
    name = windows_ui_language()
    if not name:
        try: name = locale.getlocale()[0]
        except (ValueError, TypeError): name = None
    return 'es' if (name or '').lower().replace('_', '-').split('-')[0] == 'es' else 'en'


def preference_path(root):
    return Path(root) / 'launcher-language.json'


def load_language(root):
    override = os.environ.get('NEWSNAP_LAUNCHER_LANGUAGE')
    if override in ('en', 'es'): return override
    try:
        raw = preference_path(root).read_bytes()
        value = json.loads(raw) if len(raw) <= 4096 else None
        if isinstance(value, dict) and value.get('language') in ('en', 'es'):
            return value['language']
    except (OSError, ValueError, TypeError):
        pass
    return system_language()


def set_language(value):
    global _language
    if value not in ('en', 'es'): raise ValueError('Unsupported launcher language')
    _language = value


def save_language(root, value):
    if value not in ('en', 'es'): raise ValueError('Unsupported launcher language')
    path = preference_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='launcher-language.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'language': value}, stream)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def current_language():
    return _language


def tr(text):
    return ENGLISH.get(text, text) if _language == 'en' else text
