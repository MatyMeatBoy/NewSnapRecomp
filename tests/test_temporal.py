"""A wrong camera layout must not enter temporal history."""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class TemporalTests(unittest.TestCase):
    def test_native_camera_normalization_and_rejection(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang') or str(
            ROOT / 'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe')
        if not Path(compiler).is_file() and not shutil.which(compiler):
            self.skipTest('clang is required for the native camera test')
        view=[1,0,0,-27,0,1,0,-1,0,0,1,-22,0,0,0,1]
        inverse=[1,0,0,27,0,1,0,1,0,0,1,22,0,0,0,1]
        projection=[2,0,0,0,0,3,0,0,0,0,0,0.01,0,0,-1,0]
        inv_projection=[0.5,0,0,0,0,1/3,0,0,0,0,0,-1,0,0,100,0]
        def mul(a,b):
            return [sum(a[r*4+k]*b[k*4+c] for k in range(4)) for r in range(4) for c in range(4)]
        matrices=[view,inverse,projection,inv_projection,mul(projection,view),mul(inverse,inv_projection)]
        raw=[m[c*4+r] for m in matrices for r in range(4) for c in range(4)]+[0]*90
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            fixture=folder/'camera.c'
            fixture.write_text('''#include <stdio.h>
#include "snap_temporal.h"
int main(int argc,char **argv){float raw[186],out[64];
FILE *f=fopen(argv[1],"rb");if(!f||fread(raw,sizeof raw,1,f)!=1)return 20;fclose(f);
int ok=snap_camera_decode(raw,sizeof raw,out);
if(argc>2)return ok?21:0;
if(!ok||out[3]!=-27||out[7]!=-1||out[11]!=-22||out[16]!=2||out[21]!=3||out[51]!=27)return 22;
return snap_camera_decode(raw,256,out)?23:0;}
''',encoding='utf-8')
            executable=folder/'camera.exe'
            subprocess.run([compiler,'-O2','-I',str(ROOT/'newsnap/overlays'),str(fixture),'-o',str(executable)],check=True,capture_output=True)
            cases=[(raw,False)]
            for position,value in ((0,float('nan')),(32,0),(64,77),(16,9),(48,4),(80,2)):
                changed=raw.copy();changed[position]=value;cases.append((changed,True))
            for index,(block,rejected) in enumerate(cases):
                data=folder/f'{index}.bin';data.write_bytes(struct.pack('<186f',*block))
                result=subprocess.run([str(executable),str(data)]+(['reject'] if rejected else []),capture_output=True)
                self.assertEqual(result.returncode,0,(index,result.stderr))

    def test_exact_source_seams(self):
        from newsnap.temporal_adapt import edits
        from newsnap.upstream import UPSTREAM
        for name,changes in edits().items():
            text=(UPSTREAM/name).read_text(encoding='utf-8')
            for before,after in changes:
                self.assertEqual(text.count(before),1,(name,before))
                text=text.replace(before,after,1)
