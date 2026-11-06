"""Opt-in integration experiment; never discovered by unittest. Synthetic temp data only.
Usage: python tests/run_qmd_sealed_experiment.py /absolute/path/to/pinned/npm/runtime
"""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).parents[1]))
from tools.qmd_index_experiment import build_synthetic
from tools.qmd_generation import attest,activate_synthetic,search_sealed_synthetic,verify_active,_bounded_run


def main(runtime):
    with tempfile.TemporaryDirectory(prefix='qmd-sealed-integration-') as tmp:
        base=Path(tmp);root=base/'synthetic';root.mkdir();state=base/'private';state.mkdir(mode=0o700)
        source=root/'a.md';source.write_bytes('# Synthetic\nkeyword original 中文\n'.encode('utf-8'))
        def build():
            m=build_synthetic(root=root,files=['a.md'],collection='synthetic',command=runtime/'node_modules/.bin/qmd',state_dir=state,synthetic_data_confirmed=True)
            a=attest(m,runtime_root=runtime)
            return activate_synthetic(a,state_dir=state,root=root,collection='synthetic'),m
        def search(g,runner=None):return search_sealed_synthetic('keyword',state_dir=state,root=root,collection='synthetic',expected_generation=g,_runner=runner)
        g,m=build();baseline=search(g);assert 'original 中文' in baseline['hits'][0]['text']
        live=Path(json.loads(m.read_text())['index']['path']);keepers=[]
        def wal_writer(argv,**kw):
            db=sqlite3.connect(live);keepers.append(db);db.execute('PRAGMA wal_autocheckpoint=0')
            db.execute("UPDATE content SET doc='tampered keyword'")
            db.execute("UPDATE documents_fts SET body='tampered keyword'");db.commit()
            assert Path(kw['env']['INDEX_PATH'])!=live
            return _bounded_run(argv,**kw)
        try:
            result=search(g,wal_writer)
            assert result['mode']=='qmd-keyword' and result['hits']==baseline['hits']
            print('REAL QMD + concurrent original WAL writer: identical original-source hits',flush=True)
            try:verify_active(state_dir=state,root=root,collection='synthetic',expected_generation=g)
            except ValueError:print('Tampered original generation rejected for next query',flush=True)
            else:raise AssertionError('tampered live generation accepted')
        finally:
            for db in keepers:db.close()
        g,m=build()
        def source_writer(argv,**kw):
            source.write_bytes('# Synthetic\nkeyword replacement 中文\n'.encode('utf-8'))
            return _bounded_run(argv,**kw)
        try:search(g,source_writer)
        except ValueError:print('Concurrent original source change: rejected, no stale result returned',flush=True)
        else:raise AssertionError('source mutation accepted')
        new,m=build();assert new!=g
        result=search(new);assert 'replacement 中文' in result['hits'][0]['text']
        print('Explicit new-generation rebuild + activation: updated source returned',flush=True)
        assert not list(state.glob('sealed-query-*'))
        print('Private query copies cleaned; no real vault or models used',flush=True)

if __name__=='__main__':main(Path(sys.argv[1]).resolve(strict=True))
