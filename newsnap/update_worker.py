"""Apply a staged public update from outside the installation being replaced."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .updater import UpdateError, apply_update


_LAUNCHER = 'NewSnapLauncher.exe'
_FIELDS = {'format', 'staged_folder', 'install_root', 'parent_pid', 'expected_executable'}


def _paths(staged_folder, install_root):
    source, install = Path(staged_folder), Path(install_root)
    if not source.is_absolute() or not install.is_absolute():
        raise UpdateError('Update folders must be absolute paths')
    source, install = source.resolve(), install.resolve()
    if source == install or source.is_relative_to(install) or install.is_relative_to(source):
        raise UpdateError('The update helper must be outside the installation')
    if not source.is_dir() or not install.is_dir():
        raise UpdateError('Update source or installation folder is missing')
    for path in (source / _LAUNCHER, source / 'MANIFEST.json', install / _LAUNCHER):
        if not path.is_file() or path.is_symlink():
            raise UpdateError(f'Update launcher or manifest is missing or linked: {path.name}')
    return source, install


def _pid(value):
    if type(value) is not int or not 0 < value < 1 << 32:
        raise UpdateError('Invalid parent process identifier')
    return value


def create_job(staged_folder, install_root, parent_pid):
    """Create a unique job beside the extracted release, never inside it."""
    source, install = _paths(staged_folder, install_root)
    parent_pid = _pid(parent_pid)
    job = {'format': 1, 'staged_folder': str(source), 'install_root': str(install),
           'parent_pid': parent_pid, 'expected_executable': str(install / _LAUNCHER)}
    fd, name = tempfile.mkstemp(prefix='newsnap-update-', suffix='.json', dir=source.parent)
    path = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(job, stream, indent=2)
            stream.write('\n')
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _load_job(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
        raise UpdateError('Invalid update job file')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise UpdateError('Invalid update job JSON') from exc
    if not isinstance(data, dict) or set(data) != _FIELDS or type(data['format']) is not int or data['format'] != 1:
        raise UpdateError('Unsupported update job format')
    if any(not isinstance(data[key], str) for key in ('staged_folder', 'install_root', 'expected_executable')):
        raise UpdateError('Invalid update job paths')
    source, install = _paths(data['staged_folder'], data['install_root'])
    expected = install / _LAUNCHER
    if Path(data['expected_executable']) != expected:
        raise UpdateError('The update job cannot select another executable')
    if path.resolve().is_relative_to(source) or path.resolve().is_relative_to(install):
        raise UpdateError('The update job must be outside source and installation')
    return source, install, _pid(data['parent_pid']), expected


def _wait_for_parent(parent_pid, expected_executable, *, timeout=60):
    """Wait for that launcher to exit; never terminate a user process."""
    if os.name != 'nt':
        raise UpdateError('The update worker requires Windows')
    if parent_pid == os.getpid() or not 0 <= timeout <= 60:
        raise UpdateError('Invalid update parent or timeout')
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD,
                                                 wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00100000 | 0x1000, False, parent_pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: the parent has already exited
            return True
        raise UpdateError(f'Cannot inspect the launcher process (Windows error {error})')
    try:
        if kernel.WaitForSingleObject(handle, 0) == 0:
            return True
        name = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(name))
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            raise UpdateError(f'Cannot identify the launcher process (Windows error {ctypes.get_last_error()})')
        if Path(name.value).resolve() != Path(expected_executable).resolve():
            raise UpdateError('The parent process is not the installed launcher')
        status = kernel.WaitForSingleObject(handle, int(timeout * 1000))
        if status == 0:
            return True
        if status == 258:  # WAIT_TIMEOUT
            return False
        raise UpdateError(f'Cannot wait for launcher shutdown (Windows error {ctypes.get_last_error()})')
    finally:
        kernel.CloseHandle(handle)


def _write_result(job_path, result):
    path = job_path.with_suffix('.result.json')
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def _show_error(message, result_path):
    """Keep a failed external update visible after the original UI has closed."""
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes

    user = ctypes.WinDLL('user32', use_last_error=True)
    user.MessageBoxW.argtypes = (wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT)
    user.MessageBoxW.restype = ctypes.c_int
    user.MessageBoxW(None, f'{message}\n\nRegistro: {result_path}',
                     'NewSnap · Actualización', 0x10)  # MB_OK | MB_ICONERROR


def apply_job(job_path):
    """Return 0 on applied/restarted, otherwise 1; retain the result beside the job."""
    path = Path(job_path)
    result = {'format': 1, 'status': 'error', 'applied': False}
    try:
        source, install, parent_pid, executable = _load_job(path)
        if not _wait_for_parent(parent_pid, executable, timeout=60):
            raise UpdateError('Launcher shutdown timed out; the installation was not changed')
        installed = apply_update(source, install)
        result.update(status='applied', applied=True, version=installed.version,
                      source_revision=installed.source_revision,
                      installed_files=list(installed.installed_files),
                      preserved_files=list(installed.preserved_files))
        _write_result(path, result)
        # The relaunched application must own its PyInstaller lifecycle rather
        # than inherit the staged helper's application-home/worker state.
        environment = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT='1')
        subprocess.Popen([str(executable)], cwd=install, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), env=environment)
        return 0
    except Exception as exc:
        result.update(status='error', error=str(exc))
        try:
            _write_result(path, result)
        except OSError:
            pass  # The exit code still reports failure when the sidecar cannot be written.
        message = ('La actualización se instaló, pero el launcher no pudo reiniciarse. '
                   'Ábrelo manualmente.' if result['applied'] else
                   'No se pudo instalar la actualización. La aplicación no se reiniciará automáticamente.')
        try:
            _show_error(f'{message}\n\n{exc}', path.with_suffix('.result.json'))
        except Exception:
            pass  # A failed dialog must not conceal the recorded failure or change the exit code.
        return 1
