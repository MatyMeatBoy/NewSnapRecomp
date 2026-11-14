import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsnap import home_state
from newsnap.paths import data_dir,select_data_dir


class HomeStateTests(unittest.TestCase):
    def test_complete_unmarked_inputs_are_loaded_but_not_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data,_=self.make_data(root)
            result=home_state.state(root)
            self.assertEqual(result['directory'],str(data))
            self.assertTrue(result['loaded'])
            self.assertFalse(result['verified'])
            self.assertIsNone(result['runtime_version'])

    def test_missing_sdk_is_not_loaded_even_with_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data,_=self.make_data(root)
            (data/'newsnap-game.json').write_text('{}')
            (data/'exefs/sdk').unlink()
            self.assertFalse(home_state.state(root)['loaded'])

    def make_data(self,folder):
        data=folder/'GameData';(data/'exefs').mkdir(parents=True);(data/'romfs').mkdir()
        for name in ('main','sdk'):(data/'exefs'/name).write_bytes(name.encode())
        (data/'romfs/romfs.bin').write_bytes(b'owner romfs')
        profile={'exefs_sha256':{name:hashlib.sha256(name.encode()).hexdigest() for name in ('main','sdk')},
            'romfs_sha256':hashlib.sha256(b'owner romfs').hexdigest(),
            'verified_control':{'display_version':'2.0.1','save_size':1,'journal_size':1}}
        return data,profile

    def test_loaded_is_distinct_from_verified_and_changed_bytes_need_recheck(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);data,profile=self.make_data(root)
            select_data_dir(root,data)
            with patch.object(home_state,'_profile',return_value=profile):
                self.assertTrue(home_state.state(root)['loaded'])
                self.assertFalse(home_state.state(root)['verified'])
                self.assertTrue(home_state.verify(root)['verified'])
                (data/'exefs/main').write_bytes(b'wrong main')
                self.assertFalse(home_state.state(root)['verified'])
                with self.assertRaises(ValueError):home_state.verify(root)

    def test_selection_is_portable_and_invalid_choice_preserves_current(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);root=folder/'app';root.mkdir();data,_=self.make_data(root)
            (root/'launcher-settings.json').write_text(json.dumps({'unrelated':'keep'}))
            select_data_dir(root,data)
            self.assertEqual(data_dir(root),data)
            with self.assertRaises(ValueError):select_data_dir(root,folder/'missing')
            self.assertEqual(data_dir(root),data)
            self.assertEqual(json.loads((root/'launcher-settings.json').read_text())['unrelated'],'keep')
            moved=folder/'moved';root.rename(moved)
            self.assertEqual(data_dir(moved),moved/'GameData')

    def test_external_data_is_selected_without_copying_or_touching_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);root=folder/'app';root.mkdir();owner=folder/'owner';owner.mkdir()
            data,_=self.make_data(owner);before=(data/'exefs/main').read_bytes()
            select_data_dir(root,data)
            self.assertEqual(data_dir(root),data)
            self.assertEqual((data/'exefs/main').read_bytes(),before)
            self.assertFalse((root/'GameData').exists())
