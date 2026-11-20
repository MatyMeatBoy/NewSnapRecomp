"""Optional, lossless filesystem compression for locally generated shadow DDS files.

Only new files inherit the directory setting. Existing files are never traversed
or rewritten. Unsupported filesystems keep the ordinary DDS storage path.
"""
import os
from pathlib import Path
import stat

_WINDOWS = os.name == 'nt'


def _is_reparse(part):
    try:
        info = part.lstat()
    except FileNotFoundError:
        return False
    return bool(stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400)


def _check_directory_path(folder):
    # Reject junctions as well as symbolic links, including in parent components.
    for part in (folder, *folder.parents):
        if _is_reparse(part):
            raise OSError('generated shadow directory crosses a reparse point')


def _compress_directory(folder):
    import ctypes
    from ctypes import wintypes as W

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p,
                                  W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.DeviceIoControl.argtypes = [W.HANDLE, W.DWORD, ctypes.c_void_p, W.DWORD,
                                      ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD),
                                      ctypes.c_void_p]
    kernel.DeviceIoControl.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    # BACKUP_SEMANTICS opens directories; OPEN_REPARSE_POINT avoids following
    # a final component replaced with a link between validation and opening.
    handle = kernel.CreateFileW(str(folder), 0xC0000000, 7, None, 3, 0x02200000, None)
    if handle == W.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        mode = W.USHORT(1)  # COMPRESSION_FORMAT_DEFAULT, ordinary NTFS compression
        returned = W.DWORD()
        if not kernel.DeviceIoControl(handle, 0x9C040, ctypes.byref(mode), 2,
                                      None, 0, ctypes.byref(returned), None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)


def enable_generated_compression(folder, report=print):
    """Configure the supplied generated-mod folder for new-file compression.

Returns whether Windows accepted the setting, without promising a compression
ratio. Existing DDS files and their data remain untouched. Call before creating
the generator's .part outputs. Failure is an optional storage optimization miss,
never a reason to prevent generation or playing.
"""
    if not _WINDOWS:
        return False
    folder = Path(os.path.abspath(folder))
    try:
        _check_directory_path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        _check_directory_path(folder)
        _compress_directory(folder)
    except OSError as error:
        report(f'HD shadows: optional filesystem compression unavailable ({error})')
        return False
    return True
