"""Private synthetic generation verification. Not a production enablement API."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from contextlib import closing
from .qmd_index_experiment import identity, verify_unchanged, reject_sidecars, checked_index_snapshot
from .qmd_keyword import _bounded_run, _read, _hash

# Matches the pinned 2.8.3 normalization contract, using JS Unicode Script
# properties rather than incomplete Python CJK ranges. No upstream JS is loaded.
NORMALIZER = r"""const fs=require('fs');const xs=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));const re=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]+/gu;process.stdout.write(JSON.stringify(xs.map(x=>x.replace(re,s=>' '+Array.from(s).join(' ')+' '))));"""


def runtime_digest(root):
    """Hash every regular file and safe link in an explicitly supplied runtime tree."""
    root=Path(root).resolve(strict=True)
    out=[]
    for p in sorted(root.rglob('*')):
        name=p.relative_to(root).as_posix()
        if p.is_symlink():
            target=p.resolve(strict=True)
            if not target.is_relative_to(root):raise ValueError('runtime link escapes root')
            out.append([name,'symlink',os.readlink(p)])
        elif p.is_file():
            out.append([name,'file',identity(p)['sha256']])
        elif not p.is_dir():raise ValueError('unsupported runtime entry')
    return {'root':str(root),'entries':len(out),'sha256':hashlib.sha256(json.dumps(out,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()}



def verify_fts(manifest, node):
    """Compare exact normalized FTS stored rows and check FTS index structure in RAM."""
    index=Path(manifest['index']['path'])
    with checked_index_snapshot(manifest) as db:
        db.execute('BEGIN')
        rows=db.execute('SELECT d.id,d.collection,d.path,d.title,c.doc FROM documents d JOIN content c ON d.hash=c.hash WHERE d.active=1 ORDER BY d.id').fetchall()
        # Ground expected content in authorized originals/manifest, NOT content.doc
        # alone: coherent modifications of content + FTS must still be rejected.
        sources=manifest['sources']
        observed={path:body for _,col,path,title,body in rows if col==manifest['collection']}
        if len(rows)!=len(sources) or set(observed)!=set(sources):
            raise ValueError('indexed source scope mismatch')
        for name,body in observed.items():
            if _hash(body)!=sources[name] or body!=_read(Path(manifest['root']),name) or body!=_read(Path(manifest['staging_root']),name):
                raise ValueError('indexed body differs from authorized source')
        if {row[0] for row in db.execute('SELECT doc FROM content')}!=set(observed.values()):
            raise ValueError('unexpected stored source content')
        expected=[]
        for _,col,path,title,body in rows:expected.extend([col+'/'+path,title,body])
        # Bounded harness: fail rather than produce unbounded validation payloads.
        payload=json.dumps(expected,ensure_ascii=False).encode('utf-8')
        if len(payload)>200000:raise ValueError('synthetic FTS fixture exceeds inspection limit')
        with tempfile.TemporaryDirectory(prefix='qmd-normalize-') as tmp:
            p=Path(tmp)/'input.json';p.write_bytes(payload)
            norm=json.loads(_bounded_run([str(node),'-e',NORMALIZER,str(p)]).stdout)
        if len(norm)!=len(rows)*3:raise ValueError('normalizer response mismatch')
        wanted=[(row[0],*norm[i*3:i*3+3]) for i,row in enumerate(rows)]
        actual=db.execute('SELECT rowid,filepath,title,body FROM documents_fts ORDER BY rowid').fetchall()
        if actual!=wanted:raise ValueError('FTS normalized content mismatch')
        # integrity-check is an INSERT command, so run only on an in-memory copy.
        copy=sqlite3.connect(':memory:')
        try:
            db.backup(copy)
            copy.execute("INSERT INTO documents_fts(documents_fts) VALUES('integrity-check')")
        finally:copy.close()
    if identity(index)!=manifest['index']:raise ValueError('index changed during FTS check')


def atomic_json(path,data):
    path=Path(path)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def attest(manifest_path, *, runtime_root):
    """Create evidence only. Does not select a generation or enable public search."""
    p=Path(manifest_path).resolve(strict=True)
    original=identity(p)
    m=json.loads(p.read_text(encoding='utf-8'))
    verify_unchanged(p)
    runtime=runtime_digest(runtime_root)
    if not Path(m['executable']['path']).is_relative_to(Path(runtime['root'])):
        raise ValueError('QMD executable outside bound runtime')
    node=Path(shutil.which('node') or '').resolve(strict=True)
    node_id=identity(node)
    verify_fts(m,node)
    verify_unchanged(p)
    if identity(p)!=original or runtime_digest(runtime_root)!=runtime or identity(node)!=node_id:
        raise ValueError('verification inputs changed')
    att={'schema':1,'status':'verified-synthetic-generation-only','generation':m['generation'],
         'manifest':original,'root':m['root'],'collection':m['collection'],
         'runtime':runtime,'node':node_id,'normalizer_sha256':hashlib.sha256(NORMALIZER.encode()).hexdigest()}
    result=p.parent/'attestation.json';atomic_json(result,att)
    return result


def validate_attestation(path, *, root, collection):
    p=Path(path)
    stamp=identity(p)
    a=json.loads(p.read_text(encoding='utf-8'))
    if a['status']!='verified-synthetic-generation-only' or a['root']!=str(Path(root).resolve(strict=True)) or a['collection']!=collection:
        raise ValueError('generation scope mismatch')
    if a['normalizer_sha256']!=hashlib.sha256(NORMALIZER.encode()).hexdigest():raise ValueError('normalizer changed')
    if identity(a['manifest']['path'])!=a['manifest']:raise ValueError('manifest replaced')
    m=json.loads(Path(a['manifest']['path']).read_text(encoding='utf-8'))
    if a['generation']!=m['generation'] or a['root']!=m['root'] or a['collection']!=m['collection']:
        raise ValueError('manifest binding mismatch')
    verify_unchanged(a['manifest']['path'])
    if identity(a['node']['path'])!=a['node'] or runtime_digest(a['runtime']['root'])!=a['runtime']:
        raise ValueError('runtime changed')
    verify_fts(m,Path(a['node']['path']))
    verify_unchanged(a['manifest']['path'])
    if identity(p)!=stamp:raise ValueError('attestation changed during verification')
    return a


def activate_synthetic(attestation, *, state_dir, root, collection):
    """Explicitly select validated synthetic generation; no QMD search activation."""
    state=Path(state_dir).resolve(strict=True);p=Path(attestation).resolve(strict=True)
    if not p.is_relative_to(state) or state.is_relative_to(Path(root).resolve(strict=True)):
        raise ValueError('generation outside private state')
    a=validate_attestation(p,root=root,collection=collection)
    pointer={'schema':1,'generation':a['generation'],'attestation':identity(p),'root':a['root'],'collection':collection}
    atomic_json(state/'active-synthetic.json',pointer)
    return pointer['generation']


def verify_active(*,state_dir,root,collection,expected_generation):
    state=Path(state_dir).resolve(strict=True);p=state/'active-synthetic.json'
    stamp=identity(p);pointer=json.loads(p.read_text(encoding='utf-8'))
    if pointer['generation']!=expected_generation:raise ValueError('active generation switched')
    ap=Path(pointer['attestation']['path'])
    if not ap.is_relative_to(state) or identity(ap)!=pointer['attestation']:raise ValueError('active attestation changed')
    a=validate_attestation(ap,root=root,collection=collection)
    if pointer['root']!=a['root'] or pointer['collection']!=a['collection'] or pointer['generation']!=a['generation']:
        raise ValueError('pointer binding mismatch')
    if identity(p)!=stamp:raise ValueError('active pointer changed during verification')
    return a


def search_active_synthetic(query, *, state_dir, root, collection, expected_generation):
    """Experimental E2E path: reject unverifiable generations before/after search.

    No fallback on invalid generation: caller may separately request literal search.
    This function never changes the active pointer or authorizes a real vault.
    """
    raise ValueError('synthetic live-index query disabled: no verified writer exclusion; use literal search')


def search_sealed_synthetic(query, *, state_dir, root, collection, expected_generation,
                            _runner=None):
    """Experimental query against a new private COPY, never the live generation DB.

    Scope: protects against writers of the original index, not a malicious process
    able to discover/change this process's private temporary files. Public search
    stays disabled. _runner is a test seam, not an untrusted plugin interface.
    """
    from .qmd_keyword import _search_experiment
    state=Path(state_dir).resolve(strict=True)
    pointer_path=state/'active-synthetic.json'
    pointer_stamp=identity(pointer_path)
    a=verify_active(state_dir=state,root=root,collection=collection,expected_generation=expected_generation)
    if identity(pointer_path)!=pointer_stamp:raise ValueError('generation changed before capture')
    ap=Path(json.loads(pointer_path.read_text(encoding='utf-8'))['attestation']['path'])
    astamp=identity(ap)
    mp=Path(a['manifest']['path']);m=json.loads(mp.read_text(encoding='utf-8'))
    if identity(mp)!=a['manifest']:raise ValueError('manifest changed before capture')
    with tempfile.TemporaryDirectory(prefix='sealed-query-',dir=state) as tmp:
        work=Path(tmp);(work/'config').mkdir(mode=0o700);(work/'cache').mkdir(mode=0o700)
        index=work/'index.sqlite'
        # Copy a verified immutable DB view; no live WAL is consumed.
        with checked_index_snapshot(m) as source:
            with closing(sqlite3.connect(index)) as dest:
                source.backup(dest)
                dest.execute('PRAGMA journal_mode=DELETE')
        config=Path(m['config']['path'])
        if identity(config)!=m['config']:raise ValueError('config changed before capture')
        raw=config.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=m['config']['sha256'] or identity(config)!=m['config']:
            raise ValueError('config changed while capturing')
        (work/'config'/'index.yml').write_bytes(raw)
        sealed=dict(m,index=identity(index))
        verify_fts(sealed,Path(a['node']['path']))
        captured_digest=sealed['index']['sha256']
        def pinned(argv,**kwargs):
            # Explicit Node bypasses PATH-based interpreter changes.
            return (_runner or _bounded_run)([a['node']['path'],*argv],**kwargs)
        result=_search_experiment(query,root=Path(root),files=list(m['sources']),
            enabled=True,indexed_hashes=m['sources'],collection=collection,
            command=m['executable']['path'],state_dir=work,runner=pinned)
        # QMD may update metadata in its private copy. Verify effective content,
        # not unchanged physical bytes, after the process exits and closes SQLite.
        reject_sidecars(index)
        sealed['index']=identity(index)
        verify_fts(sealed,Path(a['node']['path']))
        if {n:_hash(_read(Path(root),n)) for n in m['sources']}!=m['sources']:
            raise ValueError('original source changed during sealed query')
        if identity(pointer_path)!=pointer_stamp or identity(ap)!=astamp or identity(mp)!=a['manifest']:
            raise ValueError('generation selection/evidence changed during sealed query')
        if runtime_digest(a['runtime']['root'])!=a['runtime'] or identity(a['node']['path'])!=a['node']:
            raise ValueError('runtime changed during sealed query')
        result['experimental_generation']=expected_generation
        result['snapshot_sha256']=captured_digest
        result['snapshot_semantics']='captured generation; original sources reverified after query'
        return result
