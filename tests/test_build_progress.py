"""Real child output reaches measured progress before exit, without large builds."""
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from newsnap.progress import ProgressUpdate, coerce, parse_progress_line, ProgressTail
from newsnap.maintenance import run_build_command, MaintenanceCancelled
from newsnap.build import run_logged


class BuildProgressTests(unittest.TestCase):
    def test_measured_phase_only_and_legacy_labels(self):
        self.assertEqual(coerce('Checking').label,'Checking')
        self.assertIsNone(coerce('Checking').ratio)
        measured=ProgressUpdate('compile','Compilando',2,5)
        self.assertIs(coerce(measured),measured)
        self.assertEqual(measured.ratio,.4)
        self.assertIsNone(ProgressUpdate('link','Enlazando').ratio)
        for line in ['[2/5] CC C:/private/owner.c','\x1b[32m[2/5] CC thing\x1b[0m']:
            value=parse_progress_line(line)
            self.assertEqual((value.stage,value.current,value.total),('compile',2,5))
            self.assertEqual(value.label,'Compilando · lote actual')
            self.assertNotIn('private',value.label)
        for line in ['[7/5] bad','[1/0] bad','FATAL: private details','random output']:
            self.assertIsNone(parse_progress_line(line))
        generated=parse_progress_line('emitted 12/143 chunks, 2s')
        self.assertEqual((generated.stage,generated.current,generated.total),('generate',12,143))
        # Donor compilation starts separate Ninja invocations for each batch.
        # Expose its actual counters rather than inventing an aggregate total.
        first=parse_progress_line('[199/200] CC batch one')
        second=parse_progress_line('[1/83] CC batch two')
        self.assertEqual((first.current,first.total),(199,200))
        self.assertEqual((second.current,second.total),(1,83))
        self.assertEqual(second.ratio,1/83)

    def script(self,folder,body):
        path=folder/'child.py';path.write_text(body)
        return [sys.executable,path]

    def waiting_child(self,folder):
        ack=folder/'ack';done=folder/'done'
        command=self.script(folder,'import pathlib,time,sys\n'
            'print("[1/2] CC owner/private/file.c")\n'
            f'ack=pathlib.Path({str(ack)!r})\n'
            'deadline=time.monotonic()+3\n'
            'while not ack.exists() and time.monotonic()<deadline:time.sleep(.01)\n'
            'if not ack.exists():sys.exit(3)\n'
            'sys.stdout.write("[2/2] CC finished")\n'
            f'pathlib.Path({str(done)!r}).write_text("done")\n')
        return command,ack,done

    def test_disk_tail_emits_unflushed_child_progress_before_exit_and_drains_final_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);command,ack,done=self.waiting_child(folder)
            observed=[]
            def progress(value):
                observed.append((value,done.exists()))
                if value.current==1:ack.write_text('ack')
            run_build_command(command,folder,folder/'build.log',progress=progress)
            self.assertTrue(done.exists())
            self.assertEqual([value.current for value,_ in observed],[1,2])
            self.assertFalse(observed[0][1])
            self.assertIn('owner/private/file.c',(folder/'build.log').read_text())

    def test_inner_builder_forwards_sanitized_ninja_counts_live(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);command,ack,done=self.waiting_child(folder)
            forwarded=[]
            def display(*args,**kwargs):
                text=' '.join(map(str,args));forwarded.append(text)
                if text.startswith('[1/2]'):
                    self.assertFalse(done.exists());ack.write_text('ack')
                    self.assertTrue(kwargs.get('flush'))
            with patch('builtins.print',side_effect=display):
                run_logged(command,folder/'build.log')
            self.assertEqual(len(forwarded),2)
            self.assertFalse(any('owner/private' in line for line in forwarded))

    def test_incremental_parser_discards_oversized_lines_and_keeps_bounded_pending(self):
        observed=[];tail=ProgressTail(observed.append)
        for _ in range(200):
            tail.feed(b'X'*4096)
            self.assertLessEqual(len(tail.pending),4096)
        tail.feed(b'\n[1/3] CC first\n[2/3] CC second')
        tail.finish()
        self.assertEqual([value.current for value in observed],[1,2])

    def test_cancel_from_progress_reaps_child_and_preserves_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);late=folder/'late'
            command=self.script(folder,'import pathlib,time\nprint("[1/9] CC start")\ntime.sleep(5)\n'
                f'pathlib.Path({str(late)!r}).write_text("late")\n')
            event=threading.Event()
            with self.assertRaises(MaintenanceCancelled):
                run_build_command(command,folder,folder/'build.log',event,lambda value:event.set())
            self.assertFalse(late.exists())
            self.assertIn('[1/9]',(folder/'build.log').read_text())

    def test_failure_preserves_stderr_and_final_measured_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);observed=[]
            command=self.script(folder,'import sys\nprint("FATAL: full diagnostic",file=sys.stderr)\n'
                'sys.stdout.write("[3/4] CC last")\nsys.exit(7)\n')
            with self.assertRaisesRegex(ValueError,'7'):
                run_build_command(command,folder,folder/'build.log',progress=observed.append)
            self.assertEqual(observed[-1].current,3)
            self.assertIn('FATAL: full diagnostic',(folder/'build.log').read_text())

    def test_inner_builder_bounds_line_reads_without_losing_raw_output(self):
        from unittest.mock import Mock
        class Reader(io.StringIO):
            def readline(self,size=-1):
                self.last_size=size
                if not 0<size<=4097:raise AssertionError('unbounded stdout line read')
                return super().readline(size)
        raw='[1/2] '+'x'*100000+'\n[2/2] CC complete\n'
        stream=Reader(raw);process=Mock(stdout=stream);process.wait.return_value=0
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'build.log'
            with patch('newsnap.build.subprocess.Popen',return_value=process),\
                    patch('builtins.print') as output:
                run_logged(['builder'],path)
            self.assertEqual(path.read_text(),raw)
            self.assertEqual(output.call_count,1)
            self.assertTrue(output.call_args.args[0].startswith('[2/2]'))


if __name__=='__main__':unittest.main()
