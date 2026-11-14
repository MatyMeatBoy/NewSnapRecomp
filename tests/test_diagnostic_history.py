"""Large immediate log histories keep the newest allowlisted observations."""
import json
import os
from pathlib import Path
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
import zipfile

from newsnap import diagnostics
from newsnap.maintenance import MaintenanceCancelled


class DiagnosticHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'installation'
        self.logs=self.root/'GameData/logs';self.logs.mkdir(parents=True)
        (self.logs.parent/'newsnap-game.json').write_text('{}')
        self.destination=Path(self.temp.name)/'diagnostics.zip'

    def entry(self,name,seen):
        def metadata(*,follow_symlinks=True):
            self.assertFalse(follow_symlinks)
            self.assertTrue(diagnostics.LAUNCH_LOG.fullmatch(name) or diagnostics.DISPLAY_FILE.fullmatch(name))
            seen.append(name)
            return (self.logs/name).stat()
        return types.SimpleNamespace(name=name,stat=metadata)

    def scan(self,names,seen,event=None):
        owner=self
        class Stream:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __iter__(self):
                for index,name in enumerate(names):
                    if event is not None and index==300:event.set()
                    yield owner.entry(name,seen)
        return Stream()

    def log(self,index):
        name=f'launcher-game-20261114-120000-{index:08x}-001.log'
        path=self.logs/name;path.write_text(f'observation {index}\n')
        os.utime(path,ns=(1_000_000_000+index*1_000_000,1_000_000_000+index*1_000_000))
        return name

    def display(self,index):
        name=f'launcher-display-20261114-120000-{index:08x}-001.json'
        (self.logs/name).write_text(json.dumps({'process_id':index}))
        os.utime(self.logs/name,ns=(1_000_000_000+index*1_000_000,1_000_000_000+index*1_000_000))
        return name

    def test_recent_log_after_many_unrelated_entries_is_in_actual_zip(self):
        latest=self.log(999)
        unrelated=[f'unrelated-{i}.txt' for i in range(600)]
        for name in unrelated:(self.logs/name).write_text('PRIVATE UNRELATED')
        seen=[]
        before=(self.logs/latest).read_bytes()
        with patch.object(diagnostics.os,'scandir',return_value=self.scan([*unrelated,latest],seen)),\
                patch.object(Path,'rglob',side_effect=AssertionError('no recursive walk')):
            diagnostics.export_diagnostics(self.root,self.destination)
        with zipfile.ZipFile(self.destination) as archive:
            self.assertIn('logs/'+latest,archive.namelist())
            self.assertIn('observation 999',archive.read('logs/'+latest).decode())
            self.assertFalse(any('unrelated' in name for name in archive.namelist()))
        self.assertEqual(seen,[latest])
        self.assertEqual((self.logs/latest).read_bytes(),before)
        self.assertTrue(all((self.logs/name).read_text()=='PRIVATE UNRELATED' for name in unrelated))

    def test_streaming_heaps_select_only_four_logs_two_displays(self):
        logs=[self.log(i) for i in range(20)]
        displays=[self.display(i) for i in range(20)]
        seen=[];sizes=[]
        import heapq
        push=heapq.heappush;replace=heapq.heapreplace
        def track_push(heap,item):
            result=push(heap,item);sizes.append(len(heap));return result
        def track_replace(heap,item):
            result=replace(heap,item);sizes.append(len(heap));return result
        with patch.object(diagnostics.os,'scandir',return_value=self.scan(logs+displays,seen)),\
                patch.object(heapq,'heappush',side_effect=track_push),\
                patch.object(heapq,'heapreplace',side_effect=track_replace):
            recent,observations=diagnostics._recent_history(self.logs,None)
        self.assertEqual({path.name for _,path in recent},set(logs[-4:]))
        self.assertEqual({path.name for _,path in observations},set(displays[-2:]))
        self.assertEqual(len(seen),40)
        self.assertTrue(sizes and max(sizes)<=4)

    def test_cancel_after_old_limit_preserves_sources_and_leaves_no_output(self):
        latest=self.log(999)
        event=threading.Event();seen=[]
        names=[f'unrelated-{i}.txt' for i in range(600)]+[latest]
        with patch.object(diagnostics.os,'scandir',return_value=self.scan(names,seen,event)):
            with self.assertRaises(MaintenanceCancelled):
                diagnostics.export_diagnostics(self.root,self.destination,cancel_event=event)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.glob('.newsnap-diagnostics-*')),[])
        self.assertEqual((self.logs/latest).read_text(),'observation 999\n')


if __name__=='__main__':unittest.main()
