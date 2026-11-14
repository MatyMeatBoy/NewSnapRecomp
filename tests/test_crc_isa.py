"""Native tests of the actual adapted ISA header; no game inputs or GPU."""
import _ctypes
import ctypes
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import random
import re
import shutil
import subprocess
import struct
import tempfile
import unittest

from newsnap.crc_isa_adapt import edits
from tools.generate_crc_tables import render, tables

ROOT = Path(__file__).resolve().parents[1]


def bitwise(seed, value, width, polynomial=0xedb88320):
    result = seed & 0xffffffff
    for i in range(width):
        result ^= (value >> (8*i)) & 255
        for _ in range(8):
            result = (result >> 1) ^ (polynomial if result & 1 else 0)
    return result


class CrcIsaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = ROOT/'toolchain/astral-release/Astral Chain-Setup/llvm/bin/clang.exe'
        if not compiler.exists():
            compiler = shutil.which('clang')
        if not compiler:
            raise unittest.SkipTest('clang is required for the actual native header fixture')
        (ROOT/'build').mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT/'build', prefix='crc-isa-test-')
        cls.work = Path(cls.temp.name)
        cls.compiler = str(compiler)
        runtime = ROOT/'third_party/astral/runtime'
        for name in ['simd.h','cpu.h','patches.c']:
            source = (runtime/name).read_text()
            for old,new in edits().get('runtime/'+name, []):
                if source.count(old) != 1:
                    raise AssertionError('nonunique CRC adapter anchor: '+name)
                source = source.replace(old,new)
            (cls.work/name).write_text(source)
        for source in (ROOT/'newsnap/overlays').glob('snap_crc*'):
            shutil.copy2(source,cls.work/source.name)
        # Compile the actual patched initializer, including its no-patch build.
        (cls.work/'platform').mkdir()
        (cls.work/'platform/platform.h').write_text('')
        (cls.work/'host.h').write_text('void rt_log(const char *format, ...);\n')
        (cls.work/'cfg.h').write_text('const char *cfg_get(const char *key);\n')
        (cls.work/'fixture.c').write_text(r'''
#include "simd.h"
#include "snap_crc.h"
#include <string.h>
static const char *setting;
static int queries;
static int log_calls;
void rt_log(const char *format, ...) { log_calls++; }
const char *cfg_get(const char *key) { if (strcmp(key,"AC_SNAP_CRC32_SLICE8")) return "0"; queries++; return setting; }
void rt_patches_init(void);
void init_crc(const char *value) { setting=value; rt_patches_init(); }
int config_queries(void) { return queries; }
int startup_log_calls(void) { return log_calls; }
int enabled(void) { return snap_crc32_slice8_on; }
void select_path(int value) { snap_crc32_slice8_on=value; }
uint32_t ieee(uint64_t seed, uint64_t value, int n) { return CRC32(seed,value,n); }
uint32_t castagnoli(uint64_t seed, uint64_t value, int n) { return CRC32C(seed,value,n); }
uint32_t scalar(uint64_t seed, uint64_t value, int n) { return simd_crc(simd_crc32_tab,(uint32_t)seed,value,n); }
int evaluate_once(void) { int a=1,b=2,n=4; (void)CRC32(a++,b++,n++); return a==2 && b==3 && n==5; }
''')
        output = cls.work/'fixture.dll'
        cls.shared_flags=['-shared','-fPIC']+(['-Wl,--export-all-symbols'] if os.name=='nt' else [])
        result=subprocess.run([str(compiler),*cls.shared_flags,'-O2',
                        '-I',str(cls.work),'-I',str(runtime),str(cls.work/'fixture.c'),
                        str(cls.work/'patches.c'),str(cls.work/'snap_crc.c'),
                        str(cls.work/'snap_crc_tables.c'),'-o',str(output)],
                       capture_output=True,text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.lib = ctypes.CDLL(str(output))
        for name in ['ieee','castagnoli','scalar']:
            function = getattr(cls.lib,name)
            function.argtypes = [ctypes.c_uint64,ctypes.c_uint64,ctypes.c_int]
            function.restype = ctypes.c_uint32
        cls.lib.init_crc.argtypes=[ctypes.c_char_p]

    @classmethod
    def tearDownClass(cls):
        _ctypes.FreeLibrary(cls.lib._handle) if hasattr(_ctypes,'FreeLibrary') else _ctypes.dlclose(cls.lib._handle)
        cls.temp.cleanup()

    def test_tables_are_derived_and_reproducible(self):
        source = (ROOT/'third_party/astral/runtime/simd.h').read_text()
        base = source.split('simd_crc32_tab[256] = {',1)[1].split('};',1)[0]
        parsed = [int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',base)]
        rows = tables()
        self.assertEqual(parsed,rows[0])
        self.assertEqual((ROOT/'newsnap/overlays/snap_crc_tables.c').read_text(),render())
        for level,row in enumerate(rows):
            for byte,entry in enumerate(row):
                self.assertEqual(entry,bitwise(0,byte,level+1))

    def test_probe_default_and_startup_once_in_separate_processes(self):
        # Each process starts with BSS flag zero; never mutate production state.
        for value,wanted in [(None,1),(b'0',0),(b'1',1),(b'',1)]:
            code = ('import ctypes; l=ctypes.CDLL('+repr(str(self.work/'fixture.dll'))+'); '
                    'l.init_crc.argtypes=[ctypes.c_char_p]; '
                    'assert l.enabled()==0; l.init_crc('+repr(value)+'); '
                    'assert l.enabled()=='+str(wanted)+'; '
                    'l.init_crc(b"0" if '+str(wanted)+' else b"1"); '
                    'assert l.enabled()=='+str(wanted)+'; assert l.config_queries()==1; '
                    'assert l.startup_log_calls()==1')
            import sys
            result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_every_width_seed_and_value_bits_and_random(self):
        rng=random.Random(0xc3c32)
        cases=[(0,0),(0xffffffffffffffff,0xffffffffffffffff)]
        cases += [(1<<i,0) for i in range(64)] + [(0,1<<i) for i in range(64)]
        cases += [(rng.getrandbits(64),rng.getrandbits(64)) for _ in range(1000)]
        for enabled in [0,1]:
            self.lib.select_path(enabled)
            for n in range(9):
                for seed,value in cases:
                    self.assertEqual(self.lib.ieee(seed,value,n),bitwise(seed,value,n))
                    self.assertEqual(self.lib.castagnoli(seed,value,n),bitwise(seed,value,n,0x82f63b78))
        self.assertEqual(self.lib.evaluate_once(),1)

    def test_known_vectors_and_concurrent_immutable_reads(self):
        self.lib.select_path(1)
        first_eight=int.from_bytes(b'12345678','little')
        ieee=self.lib.ieee(0xffffffff,first_eight,8)
        castagnoli=self.lib.castagnoli(0xffffffff,first_eight,8)
        self.assertEqual(self.lib.ieee(ieee,ord('9'),1)^0xffffffff,0xcbf43926)
        self.assertEqual(self.lib.castagnoli(castagnoli,ord('9'),1)^0xffffffff,0xe3069283)
        def run(index):
            crc=0xffffffff
            for byte in b'123456789':
                crc=self.lib.ieee(crc,byte,1)
            if crc ^ 0xffffffff != 0xcbf43926:
                return False
            rng=random.Random(index)
            for _ in range(1500):
                seed,value=rng.getrandbits(32),rng.getrandbits(64)
                if self.lib.ieee(seed,value,8) != bitwise(seed,value,8):
                    return False
            return True
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.assertTrue(all(executor.map(run,range(4))))

    def test_small_constant_widths_do_not_load_startup_flag(self):
        source=self.work/'small.c'
        source.write_text('#include "simd.h"\n'
            'uint32_t one(uint32_t a,uint64_t v){return CRC32(a,v,1);}\n'
            'uint32_t two(uint32_t a,uint64_t v){return CRC32(a,v,2);}\n'
            'uint32_t castagnoli8(uint32_t a,uint64_t v){return CRC32C(a,v,8);}\n')
        assembly=self.work/'small.s'
        subprocess.run([self.compiler,'-O1','-S','-I'+str(ROOT/'third_party/astral/runtime'),
                        str(source),'-o',str(assembly)],check=True,capture_output=True)
        self.assertNotIn('snap_crc32',assembly.read_text())

    def test_cpp_consumer_links_single_c_table(self):
        source=self.work/'consumer.cpp'
        source.write_text('#include "simd.h"\nint main() { snap_crc32_init(); '
                          'return CRC32(0u,0ull,8)!=0 || sizeof(snap_crc32_slice8_rows)!=7168; }\n')
        objects=[]
        for name in ['snap_crc_tables.c','snap_crc.c']:
            obj=self.work/(name+'.o')
            subprocess.run([self.compiler,'-c',str(self.work/name),'-o',str(obj)],check=True,capture_output=True)
            objects.append(str(obj))
        # C configuration stub; the C++ caller links all three extern-C names.
        flag=self.work/'flag.c'
        flag.write_text('const char *cfg_get(const char *key) { return 0; }\n'
                       'void rt_log(const char *format, ...) {}\n')
        obj=self.work/'flag.o'
        subprocess.run([self.compiler,'-c',str(flag),'-o',str(obj)],check=True,capture_output=True)
        binary=self.work/'cpp.exe'
        result=subprocess.run([self.compiler,'-x','c++',str(source),'-x','none',str(obj),*objects,
                               '-I'+str(ROOT/'third_party/astral/runtime'),'-o',str(binary)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        subprocess.run([str(binary)],check=True,capture_output=True)

    def test_private_actual_generated_function_full_cpu_oracle(self):
        original=ROOT/'newsnapGameData/exefs/main'
        expected='ef20d6317d909bde106fec0958b58ccfdf4c46f36d9fa5ef8785ce54fff75443'
        if not original.is_file():
            self.skipTest('optional private verified original unavailable')
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),expected)
        generator=ROOT/'third_party/astral/recomp/gen.py'
        namespace={'__file__':str(generator),'__name__':'crc_private_oracle'}
        exec(compile(generator.read_text(),str(generator),'exec'),namespace)
        module=namespace['Module']('main',original,0x7000000000)
        self.assertEqual(module.nso.build_id,'ddb900ff04a912ed42430508389853cfaf1accce')
        emitter=namespace['Emitter'](module,{module.base+0x15fe90},patched={})
        lines,_=emitter.function(module.base+0x15fe90,module.base+0x15ff70)
        body='\n'.join(lines)+'\n'
        self.assertIn('CRC32(',body)
        self.assertNotIn('CRC32C(',body)
        # Two separate TUs: donor simd.h is the scalar reference regardless of
        # the gate, while the candidate includes the actual adapted header.
        objects=[]
        for name,include in [('oracle',ROOT/'third_party/astral/runtime'),('candidate',self.work)]:
            source=self.work/(name+'.c')
            source.write_text('#include "cpu.h"\n#include "simd.h"\n'+body.replace('f_700015fe90',name))
            obj=self.work/(name+'.o')
            result=subprocess.run([self.compiler,'-O1','-fPIC','-I'+str(include),
                '-I'+str(ROOT/'third_party/astral/runtime'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            objects.append(str(obj))
        stub=self.work/'oracle_stub.c'
        stub.write_text('volatile int g_fnprof;\nvoid fnprof_hit(unsigned long long a,unsigned long long b,unsigned long long c){}\nint snap_crc32_slice8_on=1;\n')
        binary=self.work/'oracle.dll'
        result=subprocess.run([self.compiler,*self.shared_flags,*objects,
             str(stub),str(self.work/'snap_crc_tables.c'),'-o',str(binary)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        library=ctypes.CDLL(str(binary))
        try:
            for name in ['oracle','candidate']:
                getattr(library,name).argtypes=[ctypes.c_void_p]
            rng=random.Random(0x15fe90)
            arena=ctypes.create_string_buffer(8192+32)
            cpu_storage=ctypes.create_string_buffer(1040)
            cpu=(ctypes.addressof(cpu_storage)+15)&~15
            address=(ctypes.addressof(arena)+15)&~15
            memory=rng.randbytes(8192)
            ctypes.memmove(address,memory,len(memory))
            count=0
            for alignment in range(16):
                for size in list(range(129))+[255,256,257,511,1023,4096,8192-16]:
                    context=bytearray(rng.randbytes(1024))
                    struct.pack_into('<Q',context,8,address+alignment)
                    struct.pack_into('<Q',context,16,size)
                    ctypes.memmove(cpu,bytes(context),1024)
                    library.oracle(cpu)
                    wanted=ctypes.string_at(cpu,1024)
                    ctypes.memmove(cpu,bytes(context),1024)
                    library.candidate(cpu)
                    self.assertEqual(ctypes.string_at(cpu,1024),wanted,(alignment,size))
                    self.assertEqual(ctypes.string_at(address,8192),memory)
                    count+=1
            self.assertEqual(count,2176)
        finally:
            _ctypes.FreeLibrary(library._handle) if hasattr(_ctypes,'FreeLibrary') else _ctypes.dlclose(library._handle)


if __name__ == '__main__':
    unittest.main()
