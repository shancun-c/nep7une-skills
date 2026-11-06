"""Bounded subprocess harness for trusted, disposable test commands.

No process enumeration, process-tree termination, permissions or Git settings.
Direct children only. File-backed output avoids descendants holding PIPE open.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

DEFAULT_TIMEOUT = 30
MAX_OUTPUT = 4 * 1024 * 1024


def run(args, *, capture_output=True, text=False, timeout=DEFAULT_TIMEOUT,
        cwd=None, env=None, encoding='utf-8', errors='replace', check=False):
    if not capture_output or timeout <= 0:
        raise ValueError('tests require captured output and a positive timeout')
    label = repr([str(a) for a in args])[:350]
    print('[test child start] '+label, file=sys.stderr, flush=True)
    with tempfile.TemporaryDirectory(prefix='test-child-output-') as tmp:
        out_path, err_path = Path(tmp)/'stdout', Path(tmp)/'stderr'
        with out_path.open('wb') as out, err_path.open('wb') as err:
            p = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=out, stderr=err)
            started = time.monotonic()
            try:
                while p.poll() is None:
                    elapsed = time.monotonic()-started
                    if elapsed >= timeout:
                        raise subprocess.TimeoutExpired(args, timeout)
                    if out_path.stat().st_size+err_path.stat().st_size > MAX_OUTPUT:
                        raise RuntimeError('test child exceeded output limit: '+label)
                    time.sleep(min(0.02, max(0.001, timeout-elapsed)))
            except BaseException:
                # Never wait indefinitely after a timeout, or bypass denied kills.
                if p.poll() is None:
                    try:
                        p.kill()
                        p.wait(timeout=5)
                    except (OSError, subprocess.TimeoutExpired) as exc:
                        print('[test child cleanup blocked] pid='+str(p.pid)+' '+type(exc).__name__,
                              file=sys.stderr, flush=True)
                        raise RuntimeError('direct test child cleanup could not be verified; pid='+str(p.pid)) from exc
                print('[test child failed/bounded] '+label,file=sys.stderr,flush=True)
                raise
        with out_path.open('rb') as stream:
            stdout = stream.read(MAX_OUTPUT+1)
        with err_path.open('rb') as stream:
            stderr = stream.read(MAX_OUTPUT+1)
        if len(stdout)+len(stderr)>MAX_OUTPUT:
            raise RuntimeError('test child exceeded output limit: '+label)
        if text:
            stdout,stderr=stdout.decode(encoding,errors),stderr.decode(encoding,errors)
        result = subprocess.CompletedProcess(args,p.returncode,stdout,stderr)
        print('[test child exit '+str(p.returncode)+'] '+label,file=sys.stderr,flush=True)
        if check:
            result.check_returncode()
        return result
