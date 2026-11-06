"""Synthetic-only index build/inspection experiment; NEVER enables public QMD search.

Content-table verification is not complete FTS verification. No readiness claim.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager, closing
try:
    from .qmd_keyword import _read, _hash, _bounded_run, _is_within
except ImportError:
    from qmd_keyword import _read, _hash, _bounded_run, _is_within


def identity(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink identity forbidden')
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            digest.update(block)
    after = path.stat()
    fields = lambda s: (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if fields(before) != fields(after):
        raise ValueError('file changed during inspection')
    return {'path': str(path.resolve()), 'stat': list(fields(after)), 'sha256': digest.hexdigest()}


def reject_sidecars(index):
    """Never treat main-file identity as complete when ANY SQLite sidecar exists."""
    for suffix in ['-wal', '-shm', '-journal']:
        p=Path(str(index)+suffix)
        if p.exists() or p.is_symlink():
            raise ValueError('SQLite sidecar present: '+suffix)


@contextmanager
def checked_index_snapshot(manifest):
    """Inspect copied main bytes immutably; never let SQLite merge an unbound WAL.

    This verifies a bounded snapshot, not a lock on live writer processes.
    """
    index=Path(manifest['index']['path'])
    reject_sidecars(index)
    if identity(index)!=manifest['index']:raise ValueError('index identity mismatch')
    if index.stat().st_size>64*1024*1024:raise ValueError('synthetic index exceeds 64 MiB')
    with index.open('rb') as source:
        raw=source.read(64*1024*1024+1)
    if len(raw)>64*1024*1024:raise ValueError('synthetic index grew beyond 64 MiB')
    if hashlib.sha256(raw).hexdigest()!=manifest['index']['sha256']:
        raise ValueError('copied index does not match manifest')
    reject_sidecars(index)
    if identity(index)!=manifest['index']:raise ValueError('index changed during copy')
    with tempfile.TemporaryDirectory(prefix='qmd-checked-index-') as tmp:
        copy=Path(tmp)/'snapshot.sqlite';copy.write_bytes(raw)
        with closing(sqlite3.connect(copy.as_uri()+'?mode=ro&immutable=1',uri=True)) as db:
            yield db
    reject_sidecars(index)
    if identity(index)!=manifest['index']:raise ValueError('index changed during verification')


def build_synthetic(*, root, files, collection, command, state_dir,
                    synthetic_data_confirmed=False):
    """Explicit developer harness only, fail closed unless synthetic scope confirmed.

    Fresh generation avoids old/untrusted config and hooks. No update, models or server.
    Failure leaves generation for diagnosis; never activates or silently reuses it.
    """
    if not synthetic_data_confirmed:
        raise ValueError('this experimental builder accepts synthetic fixtures only')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', collection):
        raise ValueError('invalid collection')
    root = Path(root).resolve(strict=True)
    command = Path(command).resolve(strict=True)
    state = Path(state_dir).resolve(strict=True)
    if _is_within(state, root):
        raise ValueError('state must be outside source root')
    if len(files) != len(set(files)) or not files:
        raise ValueError('nonempty unique allowlist required')
    before = {name: _read(root,name) for name in files}
    if any(not name.endswith('.md') for name in files):
        raise ValueError('only explicit Markdown fixtures supported')
    generation = uuid.uuid4().hex
    work = Path(tempfile.mkdtemp(prefix='generation-'+generation+'-',dir=state))
    stage = work/'source';stage.mkdir(mode=0o700)
    for name,text in before.items():
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(text.encode('utf-8'))
    for name in ['config','cache']:(work/name).mkdir(mode=0o700)
    index=work/'index.sqlite'
    env=dict(os.environ,INDEX_PATH=str(index),QMD_CONFIG_DIR=str(work/'config'),XDG_CACHE_HOME=str(work/'cache'))
    executable=identity(command)
    version=_bounded_run([str(command),'--version'],env=env,cwd=str(work)).stdout.strip()
    if version != 'qmd 2.8.3 (facd35e)':
        raise ValueError('unverified QMD version')
    _bounded_run([str(command),'collection','add',str(stage),'--name',collection],env=env,cwd=str(work),timeout=60)
    if any(_read(root,name)!=text for name,text in before.items()):
        raise ValueError('source changed while building')
    reject_sidecars(index)
    index_snapshot={'index':identity(index)}
    with checked_index_snapshot(index_snapshot) as db:
        db.execute('BEGIN')
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):
            raise ValueError('SQLite integrity failure')
        cols=db.execute('SELECT name,path,pattern,update_command FROM store_collections').fetchall()
        if cols != [(collection,str(stage),'**/*.md',None)]:
            raise ValueError('collection scope/config mismatch')
        rows=db.execute('SELECT d.collection,d.path,c.doc FROM documents d JOIN content c ON d.hash=c.hash WHERE d.active=1').fetchall()
        observed={name:doc for col,name,doc in rows if col==collection}
        if len(rows)!=len(before) or observed!=before:
            raise ValueError('actual indexed content differs from authorized snapshot')
        all_content={r[0] for r in db.execute('SELECT doc FROM content')}
        if all_content!=set(before.values()):
            raise ValueError('unexpected stored content')
        fts_paths=[r[0] for r in db.execute('SELECT filepath FROM documents_fts')]
        # Exact FTS body/token equivalence is intentionally NOT claimed.
        if sorted(fts_paths)!=sorted(collection+'/'+n for n in files):
            raise ValueError('unexpected FTS scope (non-ASCII names unsupported in this prototype)')
    if identity(command)!=executable:
        raise ValueError('executable changed')
    # Closed-QMD experimental generations must have no live/journal sidecars.
    reject_sidecars(index)
    manifest={'schema':1,'generation':generation,'root':str(root),'staging_root':str(stage),
        'collection':collection,'qmd_version':version,'executable':executable,
        'sources':{n:_hash(t) for n,t in before.items()},'index':identity(index),
        'config':identity(work/'config'/'index.yml'),
        'status':'content-verified-experimental-NOT-search-ready',
        'unverified':['FTS normalized body/token equivalence','dependency tree identity','atomic source filesystem snapshot']}
    temp=work/'manifest.tmp'
    with temp.open('x',encoding='utf-8') as f:
        json.dump(manifest,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(temp,work/'manifest.json')
    return work/'manifest.json'


def verify_unchanged(manifest_path):
    """Detect changes against one trusted manifest; does not authenticate a malicious manifest."""
    p=Path(manifest_path)
    m=json.loads(p.read_text(encoding='utf-8'))
    if m['status']!='content-verified-experimental-NOT-search-ready':
        raise ValueError('unsupported acceptance status')
    reject_sidecars(m['index']['path'])
    for key in ['index','config','executable']:
        if identity(m[key]['path']) != m[key]:
            raise ValueError(key+' replaced or changed')
    if {n:_hash(_read(Path(m['root']),n)) for n in m['sources']} != m['sources']:
        raise ValueError('original source changed')
    if {n:_hash(_read(Path(m['staging_root']),n)) for n in m['sources']} != m['sources']:
        raise ValueError('staged source changed')
    reject_sidecars(m['index']['path'])
    return False  # Even intact experimental evidence is never production readiness.
