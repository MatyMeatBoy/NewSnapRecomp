import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from newsnap.display_status import FORMAT, read_status


class DisplayStatusTests(unittest.TestCase):
    def test_timing_evidence_is_distinct_from_sync_mode_and_driver_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'display.json'
            report={'format':FORMAT,'version':1,'vk_result':0,'process_id':42,'generation':2,'observed_monotonic_ns':1234,
                'source':'none','presentation':'unknown','timing_api_available':False,
                'refresh_duration_ns':0,'refresh_interval_ns':0,'display_support':'unknown',
                'driver_enabled':'unknown','reason':'unsupported','monitor_id':'DISPLAY1',
                'monitor_name':'Test monitor','actual_present_mode':'fifo'}
            def read(**changes):
                path.write_text(json.dumps({**report,**changes}),encoding='utf-8')
                return read_status(path,42)
            self.assertEqual(read()['presentation'],'unknown')
            self.assertFalse(read(process_id=43)['available'])
            self.assertFalse(read(presentation='variable')['available'])
            valid={'source':'vulkan_ext_present_timing','timing_api_available':True,'refresh_duration_ns':16666666}
            fixed=read(**valid,presentation='fixed',refresh_interval_ns=16666666)
            self.assertEqual(fixed['presentation'],'fixed')
            self.assertEqual(fixed['driver_enabled'],'unknown')
            variable=read(**valid,presentation='variable',refresh_interval_ns=(1<<64)-1)
            self.assertEqual(variable['presentation'],'variable')
            self.assertEqual(variable['display_support'],'unknown')
            self.assertFalse(read(**valid,presentation='variable',refresh_interval_ns=16666666)['available'])
            self.assertFalse(read(**valid,presentation='fixed',refresh_interval_ns=16666666,driver_enabled='on')['available'])
            self.assertFalse(read(**valid,presentation='fixed',refresh_interval_ns=16666666,vk_result=-4)['available'])
            self.assertFalse(read(**valid,presentation='variable',refresh_interval_ns=(1<<64)-1,vk_result=True)['available'])
            self.assertFalse(read(version=True)['available'])

    def test_stale_future_oversized_and_malformed_reports_remain_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'display.json'
            path.write_text('{}');now=time.time()
            os.utime(path,(now-20,now-20))
            self.assertEqual(read_status(path,42,now=now)['reason'],'stale')
            os.utime(path,(now+100,now+100))
            self.assertEqual(read_status(path,42,now=now)['reason'],'stale')
            path.write_bytes(b'x'*4097)
            self.assertFalse(read_status(path,42)['available'])
            path.write_bytes(b'\xff')
            self.assertFalse(read_status(path,42)['available'])
            path.unlink()
            self.assertFalse(read_status(path,42)['available'])
