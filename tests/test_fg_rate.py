"""FG-02: frame generation pauses when the monitor cannot show the generated frames."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class FgRateTests(unittest.TestCase):
    def test_decision(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('clang is required for native fixtures')
        fixture = r"""
#include "snap_fg_rate.h"
#define S 1000000000ull
int main(void) {
 uint64_t since=0;
 if(!snap_fg_rate_decide(60,144,1,0,&since)) return 1;          /* 60 on 144 Hz: on */
 if(!snap_fg_rate_decide(60,120,1,0,&since)) return 2;          /* 60 on 120 Hz: on */
 if(snap_fg_rate_decide(60,100,1,1*S,&since)!=1) return 3;      /* 60 on 100 Hz: still on at first */
 if(snap_fg_rate_decide(60,100,1,2*S,&since)!=1) return 4;
 if(snap_fg_rate_decide(60,100,1,3*S+1,&since)!=0) return 5;    /* off after 2 s */
 if(snap_fg_rate_decide(60,144,0,4*S,&since)!=0) return 6;      /* back on needs 2 s too */
 if(snap_fg_rate_decide(60,144,0,6*S+1,&since)!=1) return 7;
 since=0;
 if(snap_fg_rate_decide(60,0,1,0,&since)!=1) return 8;          /* unknown refresh: allowed */
 if(snap_fg_rate_decide(120,144,1,0,&since)!=1) return 9;       /* no change requested yet */
 if(snap_fg_rate_decide(120,144,1,3*S,&since)!=0) return 10;
 return 0;
}
"""
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'f.c').write_text(fixture, encoding='utf-8')
            exe = folder / 'f.exe'
            subprocess.run([compiler, str(folder / 'f.c'), '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)],
                           check=True, capture_output=True)
            self.assertEqual(subprocess.run([str(exe)]).returncode, 0)


if __name__ == '__main__':
    unittest.main()
