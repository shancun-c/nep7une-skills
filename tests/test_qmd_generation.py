import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
sys.path.insert(0,str(Path(__file__).parents[1]))
from tools import qmd_generation as g
from tools.qmd_index_experiment import identity
from tools.qmd_keyword import _hash

@unittest.skipUnless(shutil.which('node'),'Node is required for exact Unicode normalization validation')
class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'source';self.root.mkdir()
        self.state=self.base/'private';self.state.mkdir(mode=0o700);self.work=self.state/'generation-abc';self.work.mkdir()
        stage=self.work/'source';stage.mkdir();body='中文 keyword'
        for d in [self.root,stage]:(d/'a.md').write_text(body,encoding='utf-8')
        self.runtime=self.base/'runtime';self.runtime.mkdir();(self.runtime/'qmd').write_bytes(b'synthetic executable placeholder')
        (self.work/'config').write_text('synthetic config',encoding='utf-8')
        self.index=self.work/'index.sqlite'
        with closing(sqlite3.connect(self.index)) as db, db:
            db.executescript('CREATE TABLE documents(id INTEGER,collection TEXT,path TEXT,title TEXT,hash TEXT,active INTEGER);CREATE TABLE content(hash TEXT,doc TEXT);CREATE VIRTUAL TABLE documents_fts USING fts5(filepath,title,body);')
            db.execute('INSERT INTO content VALUES (?,?)',(_hash(body),body))
            db.execute('INSERT INTO documents VALUES (1,?,?,?,?,1)',('synthetic','a.md','中文',_hash(body)))
            db.execute('INSERT INTO documents_fts(rowid,filepath,title,body) VALUES (1,?,?,?)',('synthetic/a.md',' 中 文 ',' 中 文  keyword'))
        self.m={'schema':1,'status':'content-verified-experimental-NOT-search-ready','generation':'abc','root':str(self.root),'staging_root':str(stage),'collection':'synthetic','qmd_version':'qmd 2.8.3 (facd35e)','sources':{'a.md':_hash(body)},'index':identity(self.index),'config':identity(self.work/'config'),'executable':identity(self.runtime/'qmd')}
        self.mp=self.work/'manifest.json';self.mp.write_text(json.dumps(self.m),encoding='utf-8')
    def test_exact_unicode_fts_and_integrity(self):
        g.verify_fts(self.m,Path(shutil.which('node')))
    def test_wrong_fts_body(self):
        with closing(sqlite3.connect(self.index)) as db, db:db.execute("UPDATE documents_fts SET body='wrong'")
        self.m['index']=identity(self.index)
        with self.assertRaisesRegex(ValueError,'FTS normalized'):g.verify_fts(self.m,Path(shutil.which('node')))
    def test_extra_fts_document(self):
        with closing(sqlite3.connect(self.index)) as db, db:db.execute("INSERT INTO documents_fts VALUES ('extra','extra','extra')")
        self.m['index']=identity(self.index)
        with self.assertRaisesRegex(ValueError,'FTS normalized'):g.verify_fts(self.m,Path(shutil.which('node')))
    def test_attestation_and_active_binding(self):
        a=g.attest(self.mp,runtime_root=self.runtime)
        generation=g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        self.assertEqual(g.verify_active(state_dir=self.state,root=self.root,collection='synthetic',expected_generation=generation)['generation'],'abc')
        with self.assertRaises(ValueError):g.verify_active(state_dir=self.state,root=self.root,collection='wrong',expected_generation='abc')
        with self.assertRaises(ValueError):g.verify_active(state_dir=self.state,root=self.root,collection='synthetic',expected_generation='other')
    def test_runtime_change_rejected(self):
        a=g.attest(self.mp,runtime_root=self.runtime);(self.runtime/'dependency').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError,'runtime changed'):g.validate_attestation(a,root=self.root,collection='synthetic')
    def test_manifest_replacement_rejected(self):
        a=g.attest(self.mp,runtime_root=self.runtime);raw=self.mp.read_bytes();self.mp.unlink();self.mp.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'manifest replaced'):g.validate_attestation(a,root=self.root,collection='synthetic')
    def test_config_and_source_changes_rejected(self):
        a=g.attest(self.mp,runtime_root=self.runtime);(self.work/'config').write_bytes(b'changed')
        with self.assertRaises(ValueError):g.validate_attestation(a,root=self.root,collection='synthetic')
    def test_pointer_tamper_rejected(self):
        a=g.attest(self.mp,runtime_root=self.runtime);g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        p=self.state/'active-synthetic.json';v=json.loads(p.read_text());v['collection']='wrong';p.write_text(json.dumps(v))
        with self.assertRaisesRegex(ValueError,'pointer binding'):g.verify_active(state_dir=self.state,root=self.root,collection='synthetic',expected_generation='abc')
    def test_coherent_content_and_fts_tamper_rejected(self):
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute("UPDATE content SET doc='tampered'")
            db.execute("UPDATE documents_fts SET body='tampered'")
        self.m['index']=identity(self.index)  # Even with refreshed file metadata.
        with self.assertRaisesRegex(ValueError,'authorized source'):
            g.verify_fts(self.m,Path(shutil.which('node')))
    def test_wal_tamper_main_unchanged_rejected(self):
        with closing(sqlite3.connect(self.index)) as db, db:db.execute('PRAGMA journal_mode=WAL')
        self.m['index']=identity(self.index);self.mp.write_text(json.dumps(self.m),encoding='utf-8')
        a=g.attest(self.mp,runtime_root=self.runtime)
        keeper=sqlite3.connect(self.index)
        try:
            keeper.execute('PRAGMA wal_autocheckpoint=0')
            before=identity(self.index)
            keeper.execute("UPDATE content SET doc='tampered'")
            keeper.execute("UPDATE documents_fts SET body='tampered'")
            keeper.commit()
            self.assertEqual(identity(self.index),before)
            with self.assertRaisesRegex(ValueError,'sidecar'):
                g.validate_attestation(a,root=self.root,collection='synthetic')
        finally:keeper.close()
    def test_zero_length_journal_rejected(self):
        Path(str(self.index)+'-journal').touch()
        with self.assertRaisesRegex(ValueError,'sidecar'):
            g.verify_fts(self.m,Path(shutil.which('node')))
    def test_snapshot_ignores_concurrent_wal_then_rejects(self):
        with closing(sqlite3.connect(self.index)) as db, db:db.execute('PRAGMA journal_mode=WAL')
        self.m['index']=identity(self.index)
        keeper=None
        try:
            with self.assertRaisesRegex(ValueError,'sidecar'):
                with g.checked_index_snapshot(self.m) as snapshot:
                    keeper=sqlite3.connect(self.index)
                    keeper.execute("UPDATE content SET doc='tampered'");keeper.commit()
                    self.assertEqual(snapshot.execute('SELECT doc FROM content').fetchone()[0],'中文 keyword')
        finally:
            if keeper:keeper.close()
    def test_node_environment_sanitized(self):
        env=dict(os.environ,NODE_OPTIONS='--require=/nonexistent/injected.js',NODE_PATH='/nonexistent')
        result=g._bounded_run([shutil.which('node'),'-e',"console.log(JSON.stringify([process.env.NODE_OPTIONS,process.env.NODE_PATH]))"],env=env)
        self.assertEqual(json.loads(result.stdout),[None,None])
    def test_live_query_disabled(self):
        with self.assertRaisesRegex(ValueError,'writer exclusion'):
            g.search_active_synthetic('keyword',state_dir=self.state,root=self.root,collection='synthetic',expected_generation='abc')
    def test_sealed_relative_root_and_python38_path_api(self):
        from types import SimpleNamespace
        old_cwd = Path.cwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.base)
        a = g.attest(self.mp, runtime_root=self.runtime)
        g.activate_synthetic(a, state_dir=self.state, root=self.root, collection='synthetic')
        def runner(argv, **kwargs):
            return SimpleNamespace(stdout=json.dumps([{'file':'qmd://synthetic/a.md','line':1}]))
        absolute = g.search_sealed_synthetic('keyword', state_dir=self.state,
            root=self.root, collection='synthetic', expected_generation='abc', _runner=runner)
        relative = g.search_sealed_synthetic('keyword', state_dir=Path('private'),
            root=Path('source'), collection='synthetic', expected_generation='abc', _runner=runner)
        self.assertEqual(relative['mode'], 'qmd-keyword')
        self.assertEqual(relative['hits'], absolute['hits'])
        self.assertEqual(relative['experimental_generation'], 'abc')
        self.assertEqual(list(self.state.glob('sealed-query-*')), [])

    def test_sealed_query_ignores_live_index_writer(self):
        from types import SimpleNamespace
        a=g.attest(self.mp,runtime_root=self.runtime)
        generation=g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        keeper=[]
        def writer(argv,**kw):
            self.assertNotEqual(Path(kw['env']['INDEX_PATH']),self.index)
            db=sqlite3.connect(self.index);keeper.append(db)
            db.execute('PRAGMA journal_mode=WAL')
            db.execute("UPDATE content SET doc='tampered'")
            db.execute("UPDATE documents_fts SET body='tampered'");db.commit()
            with closing(sqlite3.connect(kw['env']['INDEX_PATH'])) as sealed:
                self.assertEqual(sealed.execute('SELECT doc FROM content').fetchone()[0],'中文 keyword')
            return SimpleNamespace(stdout=json.dumps([{'file':'qmd://synthetic/a.md','line':1}]))
        try:
            result=g.search_sealed_synthetic('keyword',state_dir=self.state,root=self.root,collection='synthetic',expected_generation=generation,_runner=writer)
            self.assertEqual(result['hits'][0]['text'],'中文 keyword')
            self.assertEqual(list(self.state.glob('sealed-query-*')),[])
            with self.assertRaises(ValueError):g.verify_active(state_dir=self.state,root=self.root,collection='synthetic',expected_generation=generation)
        finally:
            for db in keeper:db.close()
    def test_sealed_query_source_change_rejected(self):
        from types import SimpleNamespace
        a=g.attest(self.mp,runtime_root=self.runtime);g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        def writer(argv,**kw):
            (self.root/'a.md').write_text('replacement keyword',encoding='utf-8')
            return SimpleNamespace(stdout='[]')
        with self.assertRaisesRegex(ValueError,'authorized source'):
            g.search_sealed_synthetic('keyword',state_dir=self.state,root=self.root,collection='synthetic',expected_generation='abc',_runner=writer)
    def test_sealed_query_pointer_switch_rejected(self):
        from types import SimpleNamespace
        a=g.attest(self.mp,runtime_root=self.runtime);g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        def writer(argv,**kw):
            p=self.state/'active-synthetic.json';body=json.loads(p.read_text());body['generation']='next';p.write_text(json.dumps(body))
            return SimpleNamespace(stdout='[]')
        with self.assertRaisesRegex(ValueError,'generation selection'):
            g.search_sealed_synthetic('keyword',state_dir=self.state,root=self.root,collection='synthetic',expected_generation='abc',_runner=writer)
    def test_sealed_copy_content_mutation_rejected(self):
        from types import SimpleNamespace
        a=g.attest(self.mp,runtime_root=self.runtime);g.activate_synthetic(a,state_dir=self.state,root=self.root,collection='synthetic')
        def writer(argv,**kw):
            with closing(sqlite3.connect(kw['env']['INDEX_PATH'])) as db, db:
                db.execute("UPDATE content SET doc='tampered'")
                db.execute("UPDATE documents_fts SET body='tampered'")
            return SimpleNamespace(stdout='[]')
        with self.assertRaisesRegex(ValueError,'authorized source'):
            g.search_sealed_synthetic('keyword',state_dir=self.state,root=self.root,collection='synthetic',expected_generation='abc',_runner=writer)
    def test_runtime_escape_symlink(self):
        p=self.runtime/'escape'
        try:p.symlink_to(self.mp)
        except (OSError,NotImplementedError) as e:self.skipTest(str(e))
        with self.assertRaisesRegex(ValueError,'escapes'):g.runtime_digest(self.runtime)

if __name__=='__main__':unittest.main()
