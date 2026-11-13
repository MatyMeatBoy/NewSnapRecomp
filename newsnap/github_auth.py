"""Optional private-repository access; tokens never enter game data or logs."""
import os
import re
import shutil
import subprocess

TARGET = 'NewSnapRecomp:github:MatyMeatBoy/NewSnapRecomp'


def _valid(token):
    token = token.strip()
    if not token or len(token) > 1024 or not re.fullmatch(r'[A-Za-z0-9_]+', token):
        raise ValueError('El token de GitHub tiene un formato no válido.')
    return token


def _credential_api():
    if os.name != 'nt':
        raise ValueError('El almacenamiento de credenciales requiere Windows.')
    import ctypes
    from ctypes import wintypes

    class Credential(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                    ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                    ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                    ('CredentialBlob', ctypes.POINTER(wintypes.BYTE)), ('Persist', wintypes.DWORD),
                    ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                    ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    api.CredReadW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(ctypes.POINTER(Credential)))
    api.CredReadW.restype = wintypes.BOOL
    api.CredWriteW.argtypes = (ctypes.POINTER(Credential), wintypes.DWORD)
    api.CredWriteW.restype = wintypes.BOOL
    api.CredDeleteW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD)
    api.CredDeleteW.restype = wintypes.BOOL
    api.CredFree.argtypes = (ctypes.c_void_p,)
    api.CredFree.restype = None
    return ctypes, wintypes, Credential, api


def _stored_token(target=TARGET):
    if os.name != 'nt':
        return None
    ctypes, _, Credential, api = _credential_api()
    pointer = ctypes.POINTER(Credential)()
    if not api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
        if ctypes.get_last_error() == 1168:  # ERROR_NOT_FOUND
            return None
        raise OSError('No se pudo leer la credencial de GitHub de Windows.')
    try:
        value = pointer.contents
        if not 0 < value.CredentialBlobSize <= 1024:
            raise ValueError('La credencial de GitHub almacenada no es válida.')
        return _valid(ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize).decode('ascii'))
    finally:
        api.CredFree(pointer)


def _write_stored(token, target=TARGET):
    token = _valid(token)
    ctypes, wintypes, Credential, api = _credential_api()
    blob = (wintypes.BYTE * len(token)).from_buffer_copy(token.encode('ascii'))
    value = Credential(Type=1, TargetName=target, CredentialBlobSize=len(token),
                       CredentialBlob=blob, Persist=2, UserName='GitHub')
    if not api.CredWriteW(ctypes.byref(value), 0):
        raise OSError('No se pudo guardar la credencial de GitHub en Windows.')


def _delete_stored(target=TARGET):
    ctypes, _, _, api = _credential_api()
    if not api.CredDeleteW(target, 1, 0) and ctypes.get_last_error() != 1168:
        raise OSError('No se pudo quitar la credencial de GitHub de Windows.')


def save_token(token):
    _write_stored(_valid(token))


def remove_token():
    _delete_stored()


def _cli_token():
    command = shutil.which('gh')
    if not command:
        return None
    try:
        process = subprocess.run([command, 'auth', 'token', '--hostname', 'github.com'],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 timeout=3, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if process.returncode == 0:
            return _valid(process.stdout.decode('ascii'))
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        pass
    return None


def get_token():
    for name in ('GH_TOKEN', 'GITHUB_TOKEN'):
        token = os.environ.get(name)
        if token:
            return _valid(token)
    return _stored_token() or _cli_token()
