"""Synthetic SQLite/Node inspection envelope, NOT a real QMD indexing benchmark.
Run: python tests/run_qmd_inspection_scale.py > result.json
No install, real vault, service, model, or production activation.
"""
import json
import platform
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
from contextlib import closing
sys.path.insert(0, str(Path(__file__).parents[1]))
from tools.qmd_index_experiment import identity
from tools.qmd_keyword import _hash, _bounded_run
from tools.qmd_generation import verify_fts, NORMALIZER, NORMALIZER_TOTAL_BYTES, NORMALIZER_MAX_ROWS


def case(count, repetitions):
    node = shutil.which('node')
    if not node:
        raise RuntimeError('existing Node required; no automatic install')
    with tempfile.TemporaryDirectory(prefix='synthetic-fts-scale-') as tmp:
        base = Path(tmp)
        root, stage = base/'source', base/'staged'
        root.mkdir(); stage.mkdir()
        docs = []
        for i in range(count):
            body = '# Synthetic %d\n' % i + ('中文检索 evidence risk latency 合成数据\n' * repetitions)
            name = 'note-%04d.md' % i
            for folder in [root, stage]:
                (folder/name).write_bytes(body.encode('utf-8'))
            docs.append((i+1, name, body))
        expected = [value for _, name, body in docs for value in ['synthetic/'+name, name, body]]
        payload = json.dumps(expected, ensure_ascii=False).encode('utf-8')
        input_path = base/'normalize.json'; input_path.write_bytes(payload)
        # Build the exact expected fixture with the existing pinned normalization
        # contract, not a claim that the third-party QMD indexer produced it.
        normalized = json.loads(_bounded_run([node, '-e', NORMALIZER, str(input_path)], max_bytes=4000000).stdout)
        index = base/'index.sqlite'
        with closing(sqlite3.connect(index)) as db, db:
            db.executescript('CREATE TABLE documents(id INTEGER,collection TEXT,path TEXT,title TEXT,hash TEXT,active INTEGER);CREATE TABLE content(hash TEXT,doc TEXT);CREATE VIRTUAL TABLE documents_fts USING fts5(filepath,title,body);')
            for offset, (number, name, body) in enumerate(docs):
                db.execute('INSERT INTO content VALUES (?,?)', (_hash(body), body))
                db.execute('INSERT INTO documents VALUES (?,?,?,?,?,1)', (number, 'synthetic', name, name, _hash(body)))
                db.execute('INSERT INTO documents_fts(rowid,filepath,title,body) VALUES (?,?,?,?)', (number, *normalized[offset*3:offset*3+3]))
        manifest = {'index':identity(index), 'root':str(root), 'staging_root':str(stage), 'collection':'synthetic', 'sources':{name:_hash(body) for _,name,body in docs}}
        start = time.perf_counter()
        try:
            verify_fts(manifest, Path(node))
            status = 'accepted'
        except ValueError as exc:
            status = str(exc)
        elapsed = time.perf_counter()-start
        expected_status = 'accepted'
        if count > NORMALIZER_MAX_ROWS:
            expected_status = 'normalizer row budget exceeded'
        elif sum(len(json.dumps(expected[i:i+3], ensure_ascii=False).encode('utf-8')) for i in range(0,len(expected),3)) > NORMALIZER_TOTAL_BYTES:
            expected_status = 'normalizer cumulative input budget exceeded'
        if status != expected_status:
            raise AssertionError((status, expected_status))
        tamper = None
        if status == 'accepted':
            with closing(sqlite3.connect(index)) as db, db:
                db.execute('UPDATE documents_fts SET body=? WHERE rowid=?', ('substituted', count))
            manifest['index'] = identity(index)
            try:
                verify_fts(manifest, Path(node))
            except ValueError as exc:
                tamper = str(exc)
            else:
                raise AssertionError('last-document FTS substitution accepted')
            if tamper != 'FTS normalized content mismatch':
                raise AssertionError(tamper)
        return {'documents':count, 'body_repetitions':repetitions, 'payload_bytes':len(payload), 'database_bytes':index.stat().st_size, 'inspection_seconds':round(elapsed,6), 'status':status, 'last_document_tamper':tamper}


def main():
    result = {'scope':'synthetic SQLite FTS5 + existing Node normalization; not QMD retrieval', 'python':platform.python_version(), 'sqlite':sqlite3.sqlite_version, 'node':_bounded_run([shutil.which('node'), '--version']).stdout.strip(), 'cases':[case(n,8) for n in [32,128,512]]}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
