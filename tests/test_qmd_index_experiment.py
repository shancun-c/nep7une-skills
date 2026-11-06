import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import sqlite3
from contextlib import closing
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import qmd_index_experiment as m

class IndexEvidenceTests(unittest.TestCase):
    def test_requires_explicit_synthetic_scope(self):
        with self.assertRaises(ValueError):
            m.build_synthetic(root='unused',files=[],collection='x',command='unused',state_dir='unused')
    def test_manifest_never_enables_and_detects_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);source=r/'source';stage=r/'stage';source.mkdir();stage.mkdir()
            for d in [source,stage]:(d/'a.md').write_text('中文',encoding='utf-8')
            for f in ['index','config','exe']:(r/f).write_bytes(b'fixture')
            manifest={'status':'content-verified-experimental-NOT-search-ready','root':str(source),'staging_root':str(stage),'sources':{'a.md':m._hash('中文')},'index':m.identity(r/'index'),'config':m.identity(r/'config'),'executable':m.identity(r/'exe')}
            p=r/'manifest.json';p.write_text(json.dumps(manifest),encoding='utf-8')
            self.assertIs(m.verify_unchanged(p),False)
            (r/'index').unlink();(r/'index').write_bytes(b'fixture')
            with self.assertRaises(ValueError):m.verify_unchanged(p)
    def test_detects_config_and_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);(r/'data').write_bytes(b'original');stamp=m.identity(r/'data')
            (r/'data').write_bytes(b'changed');self.assertNotEqual(stamp,m.identity(r/'data'))
    def test_snapshot_connection_closed_on_success_and_error(self):
        class Tracked(sqlite3.Connection):
            was_closed=False
            def close(self):
                self.was_closed=True
                return super().close()
        with tempfile.TemporaryDirectory() as tmp:
            index=Path(tmp)/'index.sqlite'
            with closing(sqlite3.connect(index)) as db, db:
                db.execute('CREATE TABLE fixture(value TEXT)')
                db.execute("INSERT INTO fixture VALUES ('synthetic')")
            manifest={'index':m.identity(index)}
            connect=sqlite3.connect
            for fail in [False,True]:
                seen=[]
                def tracked(*args,**kwargs):
                    c=connect(*args,**kwargs,factory=Tracked);seen.append(c);return c
                with patch.object(m.sqlite3,'connect',side_effect=tracked):
                    try:
                        with m.checked_index_snapshot(manifest) as snapshot:
                            self.assertEqual(snapshot.execute('SELECT value FROM fixture').fetchone()[0],'synthetic')
                            if fail:raise RuntimeError('injected inspection failure')
                    except RuntimeError:
                        if not fail:raise
                self.assertEqual(len(seen),1)
                self.assertTrue(seen[0].was_closed)
                with self.assertRaises(sqlite3.ProgrammingError):seen[0].execute('SELECT 1')
if __name__=='__main__':unittest.main()
