"""Standalone launcher entry point; no game code/data embedded in the release."""
import os
import sys
from pathlib import Path


def main():
    from newsnap.upstream import ROOT
    from newsnap.paths import runtime_dir
    os.chdir(ROOT)
    from newsnap import recomplauncher
    if recomplauncher.handles(sys.argv[1:]):
        return recomplauncher.main(sys.argv[1:], ROOT)
    if getattr(sys, 'frozen', False):   # an installed launcher: drop what earlier releases shipped beside it
        from newsnap.updater import remove_retired_files
        remove_retired_files(ROOT)
    if '--apply-update' in sys.argv[1:]:
        from newsnap.update_worker import apply_job
        if len(sys.argv) != 3 or sys.argv[1] != '--apply-update':
            return 1
        return apply_job(Path(sys.argv[2]))
    if '--prepare' in sys.argv[1:]:
        from newsnap.shaders import prepare_observed
        logs = runtime_dir(ROOT) / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        original_streams = sys.stdout, sys.stderr
        with (logs / 'launcher-prepare-worker.log').open('a', encoding='utf-8', buffering=1) as log:
            sys.stdout = sys.stderr = log
            try:
                prepare_observed(runtime_dir(ROOT), '--all' in sys.argv[1:])
                from newsnap.launcher_settings import clear_shader_preparation_required
                clear_shader_preparation_required(ROOT)   # prepared: the next start needs no preparation
            except Exception:
                import traceback
                traceback.print_exc()
                return 1
            finally:
                sys.stdout, sys.stderr = original_streams
        return 0
    if '--selftest-launcher' in sys.argv[1:]:
        import tkinter
        from newsnap.launcher import Launcher
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            window = tkinter.Tk()
            window.withdraw()
            Launcher(window, Path(folder), check_updates=False)
            window.update_idletasks()
            window.destroy()
        return 0
    if '--selftest-data' in sys.argv[1:]:
        from newsnap.saves import local_save_key
        from newsnap.launcher_settings import validate_runtime_data
        try:
            validate_runtime_data(ROOT)
            if len(local_save_key()) != 16:
                return 1
        except Exception:
            return 1
        return 0
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MatyMeatBoy.NewSnapRecomp.Launcher')
    from newsnap.launcher import main as launcher_main
    launcher_main()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
