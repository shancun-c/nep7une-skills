"""Experimental QMD keyword prototype; public activation is blocked pending verified indexing."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import queue
import threading
import time
from types import SimpleNamespace
from typing import Dict, List, Optional
from urllib.parse import unquote, urlsplit

MAX_BYTES = 1_000_000


def _bounded_run(argv, *, env=None, cwd=None, timeout=10, max_bytes=MAX_BYTES):
    """Bound stdout in bytes while reading; discard stderr rather than retaining it.

    No shell. Trusted executable only; this is not a hostile process sandbox.
    """
    env = dict(os.environ if env is None else env)
    for key in ['NODE_OPTIONS', 'NODE_PATH']:
        env.pop(key, None)
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, env=env, cwd=cwd)
    chunks = queue.Queue(maxsize=2)
    stop = threading.Event()
    def read_stdout():
        try:
            while not stop.is_set():
                part = p.stdout.read(4096)
                while not stop.is_set():
                    try:
                        chunks.put(part, timeout=0.05)
                        break
                    except queue.Full:
                        pass
                if not part:
                    break
        finally:
            p.stdout.close()
    worker = threading.Thread(target=read_stdout, daemon=True)
    worker.start()
    end, data = time.monotonic() + timeout, bytearray()
    try:
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(argv, timeout)
            try:
                chunk = chunks.get(timeout=remaining)
            except queue.Empty:
                raise subprocess.TimeoutExpired(argv, timeout)
            if not chunk:
                break
            if len(data) + len(chunk) > max_bytes:
                raise ValueError('stdout limit exceeded')
            data.extend(chunk)
        code = p.wait(timeout=max(0.001, end-time.monotonic()))
        if code:
            raise subprocess.CalledProcessError(code, argv)
        return SimpleNamespace(stdout=data.decode('utf-8', errors='strict'))
    finally:
        stop.set()
        if p.poll() is None:
            p.kill()
        p.wait(timeout=5)
        worker.join(timeout=1)


def search(query: str, **kwargs) -> dict:
    """Public adapter: QMD execution blocked pending trusted index binding workflow.

    Enabling QMD is not supported yet. Only explicit-scope literal fallback runs.
    _search_experiment is test-only, never a production activation mechanism.
    """
    requested = kwargs.pop('enabled', False)
    result = _search_experiment(query, enabled=False, **kwargs)
    if requested:
        result['reason'] = 'qmd-experimental-index-binding-unimplemented'
    return result


def _is_within(path: Path, root: Path) -> bool:
    """Lexical containment for already-canonical paths, compatible with Python 3.8."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read(root: Path, relative: str) -> str:
    p = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('unsafe path')
    # Reject links even when they currently point inside the root.
    if any((root.joinpath(*Path(relative).parts[:i])).is_symlink()
           for i in range(1, len(Path(relative).parts) + 1)):
        raise ValueError('symlink')
    if not _is_within(p.resolve(), root) or not p.is_file():
        raise ValueError('unavailable source')
    with p.open('rb') as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('oversized source')
    return raw.decode('utf-8')


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _search_experiment(query: str, *, root: Path, files: List[str], enabled: bool = False,
           indexed_hashes: Optional[Dict[str, str]] = None, collection: str = 'authorized',
           command: str = 'qmd', state_dir: Optional[Path] = None, limit: int = 5,
           runner=None) -> dict:
    """No installation, indexing, mutation, models or server. Root is explicit consent scope.

    indexed_hashes must come from a trusted successfully completed indexing workflow,
    not freshly computed and falsely labelled as indexed. Missing/stale snapshots fail
    closed to literal matching. Empty QMD results stay empty.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 512 or query.startswith('-'):
        raise ValueError('nonempty keyword query required; no option-like input')
    if not 1 <= limit <= 20 or not collection or '/' in collection:
        raise ValueError('invalid limit or collection')
    root = Path(root).resolve(strict=True)
    documents, unavailable = {}, []
    for name in dict.fromkeys(files):
        try:
            documents[name] = _read(root, name)
        except (OSError, ValueError, UnicodeError):
            unavailable.append(name)
    def literal(reason):
        hits = []
        for name, text in documents.items():
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if query.casefold() in line.casefold():
                    hits.append({'file': name, 'line': i + 1, 'text': '\n'.join(lines[max(0,i-1):i+2])})
                    break
            if len(hits) == limit:
                break
        return {'mode': 'literal', 'reason': reason, 'hits': hits, 'unavailable': unavailable}
    if not enabled:
        return literal('qmd-disabled')
    hashes = {name: _hash(text) for name, text in documents.items()}
    if unavailable or hashes != indexed_hashes:
        return literal('index-snapshot-missing-or-stale')
    if state_dir is None:
        return literal('private-state-not-configured')
    state = Path(state_dir).resolve()
    if _is_within(state, root) or not state.is_dir():
        return literal('unsafe-state-directory')
    env = dict(os.environ, INDEX_PATH=str(state / 'index.sqlite'),
               QMD_CONFIG_DIR=str(state / 'config'), XDG_CACHE_HOME=str(state / 'cache'))
    try:
        p = (runner or _bounded_run)([command, 'search', query, '--json', '-n', str(limit), '-c', collection],
                   timeout=10, env=env, cwd=str(state))
        if len(p.stdout) > MAX_BYTES:
            raise ValueError('oversized response')
        rows = json.loads(p.stdout)
        if not isinstance(rows, list) or len(rows) > limit:
            raise ValueError('invalid response')
        hits, seen = [], set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('file'), str):
                raise ValueError('invalid result')
            uri = urlsplit(row['file'])
            name = unquote(uri.path.lstrip('/'))
            if uri.scheme != 'qmd' or uri.netloc != collection or uri.query or uri.fragment or name not in documents:
                raise ValueError('out-of-scope result')
            line = row.get('line')
            if type(line) is not int or line < 1:
                raise ValueError('invalid source line')
            original = _read(root, name)
            if _hash(original) != hashes[name]:
                raise ValueError('source changed during search')
            lines = original.splitlines()
            if line > len(lines):
                raise ValueError('source line unavailable')
            if name not in seen:
                hits.append({'file': name, 'line': line, 'text': '\n'.join(lines[max(0,line-2):line+1])})
                seen.add(name)
        # Check EVERY authorized source even for empty results or non-hit changes.
        if {name: _hash(_read(root, name)) for name in dict.fromkeys(files)} != hashes:
            raise ValueError('authorized source set changed during search')
        return {'mode': 'qmd-keyword', 'reason': None, 'hits': hits, 'unavailable': unavailable}
    except (OSError, subprocess.SubprocessError, ValueError, UnicodeError, TypeError):
        # Re-read sources so fallback does not serve the pre-search snapshot after a race.
        documents.clear()
        for name in dict.fromkeys(files):
            try:
                documents[name] = _read(root, name)
            except (OSError, ValueError, UnicodeError):
                if name not in unavailable:
                    unavailable.append(name)
        return literal('qmd-failed-or-source-unverified')
