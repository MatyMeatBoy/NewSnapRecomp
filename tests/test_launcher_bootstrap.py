from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class WritableBootstrapTests(unittest.TestCase):
    def test_writable_root_keeps_normal_dispatch(self):
        from newsnap.launcher_bootstrap import relocate_if_needed
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch('newsnap.launcher_bootstrap.writable_install',return_value=root), \
                 patch('newsnap.launcher_bootstrap.subprocess.run') as run:
                self.assertIsNone(relocate_if_needed(root,['--play']))
                run.assert_not_called()

    def test_relocation_forwards_arguments_handles_and_exit_without_mutating_source(self):
        from newsnap.launcher_bootstrap import relocate_if_needed
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'original';root.mkdir();target=Path(temporary)/'local';target.mkdir()
            language=root/'launcher-language.json';language.write_text('{"language":"es"}')
            before=language.read_bytes()
            with patch('newsnap.launcher_bootstrap.writable_install',return_value=target), \
                 patch('newsnap.launcher_bootstrap.subprocess.run') as run:
                run.return_value.returncode=75
                self.assertEqual(relocate_if_needed(root,['--recomplauncher-play','--set=fps=144']),75)
                self.assertEqual(run.call_args.args[0],[str(target/'NewSnapLauncher.exe'),'--recomplauncher-play','--set=fps=144'])
                self.assertFalse(run.call_args.kwargs['close_fds'])
                self.assertEqual(language.read_bytes(),before)
                self.assertEqual((target/'launcher-language.json').read_bytes(),before)

    def test_relocated_relative_inputs_keep_original_install_meaning(self):
        from newsnap.launcher_bootstrap import relocate_if_needed
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'original';root.mkdir();target=Path(temporary)/'local';target.mkdir()
            with patch('newsnap.launcher_bootstrap.writable_install',return_value=target), \
                 patch('newsnap.launcher_bootstrap.subprocess.run') as run:
                run.return_value.returncode=0
                relocate_if_needed(root,['--recomplauncher-prepare','--game=GameData','--keys','prod.keys'])
                self.assertIn('--game='+str(root/'GameData'),run.call_args.args[0])
                self.assertEqual(run.call_args.args[0][-1],str(root/'prod.keys'))
