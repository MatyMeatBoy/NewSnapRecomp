import importlib
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class FpsRailTests(unittest.TestCase):
    def module(self):
        self.assertTrue((ROOT/'tools/check_fps_rail.py').is_file(), 'rail comparison tool missing')
        return importlib.import_module('tools.check_fps_rail')

    def test_crossings_are_by_progress_and_wall_time(self):
        m=self.module()
        text='\n'.join(f'[host] snap_rail: object abc wall_ns {int(t*1e9)} elapsed_ns 0 progress {p} length 116'
                       for t,p in [(20,0),(30,10),(80,60),(120,100),(130,110)])
        self.assertAlmostEqual(m.rail_seconds(text,10,100),90)
        with self.assertRaises(ValueError):m.rail_seconds(text,10,115)
        # A reset cannot be bridged to fabricate a completed traversal.
        reset=text.replace('progress 100','progress 1').replace('progress 110','progress 11')
        with self.assertRaises(ValueError):m.rail_seconds(reset,10,100)

    def test_comparison_rejects_mixed_builds_saves_or_cache(self):
        m=self.module()
        base={'native_sha256':'a','route_sha256':'r','seed_hashes':{'slot':'s'},
              'gpu_identity':'fixture',
              'cache_seed_hashes':{'shader':'c'},'exit_code':0,'source_unchanged':True,
              'settings':{'AC_FPS':'60','AC_RENDER_SCALE':'100'}}
        other=dict(base,settings=dict(base['settings'],AC_FPS='144'))
        m.comparable(base,other)
        for key,value in [('native_sha256','b'),('seed_hashes',{'slot':'x'}),
                          ('cache_seed_hashes',{'shader':'x'}),('source_unchanged',False),('exit_code',1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                m.comparable(base,dict(other,**{key:value}))


if __name__=='__main__':unittest.main()
