import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import process_helper
from process_helper import run

class ProcessLimits(unittest.TestCase):
    def test_timeout_terminates_direct_child_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp)/'late'
            command=[sys.executable,'-c',"import time,pathlib;time.sleep(1);pathlib.Path(%r).write_text('late')" % str(marker)]
            start=time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):run(command,timeout=0.1)
            self.assertLess(time.monotonic()-start,6)
            time.sleep(1.1)
            self.assertFalse(marker.exists())
    def test_captured_utf8_and_nonzero(self):
        r=run([sys.executable,'-c',"import sys;sys.stdout.buffer.write('中文'.encode('utf-8'));sys.stderr.write('err');sys.exit(3)"],text=True)
        self.assertEqual((r.returncode,r.stdout,r.stderr),(3,'中文','err'))
    def test_output_limit_stops_running_child(self):
        command=[sys.executable,'-c',"import sys,time;sys.stdout.buffer.write(b'x'*2048);sys.stdout.flush();time.sleep(2)"]
        with patch.object(process_helper,'MAX_OUTPUT',1024):
            with self.assertRaisesRegex(RuntimeError,'output limit'):run(command,timeout=5)
    def test_output_limit_checks_exited_child(self):
        with patch.object(process_helper,'MAX_OUTPUT',1024):
            with self.assertRaisesRegex(RuntimeError,'output limit'):
                run([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'x'*2048)"])
    def test_no_input_prompt_and_progress(self):
        log=io.StringIO()
        with contextlib.redirect_stderr(log):
            r=run([sys.executable,'-c','import sys;print(len(sys.stdin.read()))'],text=True)
        self.assertEqual(r.stdout.strip(),'0')
        self.assertIn('test child start',log.getvalue());self.assertIn('test child exit 0',log.getvalue())

if __name__=='__main__':unittest.main()
