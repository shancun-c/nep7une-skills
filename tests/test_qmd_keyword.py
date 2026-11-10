import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import sys
import unittest
from unittest import mock
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('qmd_keyword', Path(__file__).parents[1] / 'tools/qmd_keyword.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class QmdTests(unittest.TestCase):
    def test_python38_containment_preserves_boundaries(self):
        self.assertTrue(m._is_within(self.root, self.root))
        self.assertTrue(m._is_within(self.root / 'a.md', self.root))
        self.assertFalse(m._is_within(self.root.parent, self.root))
        self.assertFalse(m._is_within(self.root.with_name(self.root.name + '-other'), self.root))
        self.assertEqual(m._read(self.root, 'a.md'), '# Synthetic\n关键词 keyword\n')

    def test_no_python39_path_api_in_qmd_modules(self):
        import ast
        for name in ['qmd_keyword.py', 'qmd_index_experiment.py', 'qmd_generation.py']:
            source = Path(__file__).parents[1] / 'tools' / name
            tree = ast.parse(source.read_text(encoding='utf-8'))
            self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr == 'is_relative_to'
                                 for node in ast.walk(tree)), name)

    def test_pr_python38_syntax_and_known_api_regressions(self):
        # A focused guard, not a substitute for running the actual 3.8 CI matrix.
        import ast
        root = Path(__file__).parents[1]
        files = ['tools/qmd_keyword.py', 'tools/qmd_index_experiment.py',
                 'tools/qmd_generation.py', 'tests/test_qmd_keyword.py',
                 'tests/test_qmd_index_experiment.py', 'tests/test_qmd_generation.py',
                 'tests/run_qmd_sealed_experiment.py', 'tests/process_helper.py',
                 'tests/test_subprocess_limits.py', 'tests/test_canvas_safety.py',
                 'tests/test_dependencies.py', 'tests/test_git_policy.py',
                 'tests/test_install_safety.py', 'tests/test_python_install_smoke.py']
        forbidden = {'is_relative_to', 'removeprefix', 'removesuffix', 'is_junction'}
        for name in files:
            tree = ast.parse((root / name).read_text(encoding='utf-8'), feature_version=8)
            for node in ast.walk(tree):
                # These files need no bitwise OR. Reject dict union (3.9+) and
                # evaluated union type expressions (3.10+) alike.
                self.assertFalse(isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr), name)
                self.assertFalse(isinstance(node, ast.Attribute) and node.attr in forbidden, name)

    def test_search_options_merge_without_mutating_defaults(self):
        before = dict(self.args)
        result = self.run_search(enabled=False)
        self.assertEqual(result['mode'], 'literal')
        self.assertEqual(self.args, before)
        self.assertNotIn('enabled', self.args)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'synthetic'; self.root.mkdir()
        self.state = self.base / 'private'; self.state.mkdir(mode=0o700)
        (self.root / 'a.md').write_bytes('# Synthetic\n关键词 keyword\n'.encode('utf-8'))
        self.args = dict(root=self.root, files=['a.md'], state_dir=self.state,
                         indexed_hashes={'a.md': m._hash(m._read(self.root, 'a.md'))})
        self.calls = []
    def runner(self, argv, **kw):
        self.calls.append((argv, kw))
        return SimpleNamespace(stdout=json.dumps([{'file':'qmd://authorized/a.md','line':2,'snippet':'UNTRUSTED'}]))
    def run_search(self, **kw):
        return m._search_experiment('keyword', **({**self.args, 'enabled':True, 'runner':self.runner, **kw}))
    def test_disabled_never_calls_qmd(self):
        x=self.run_search(enabled=False);self.assertEqual(x['reason'],'qmd-disabled');self.assertFalse(self.calls)
    def test_success_rereads_source(self):
        x=self.run_search();self.assertEqual(x['mode'],'qmd-keyword');self.assertNotIn('UNTRUSTED',str(x));self.assertIn('keyword',x['hits'][0]['text'])
        self.assertEqual(self.calls[0][0],['qmd','search','keyword','--json','-n','5','-c','authorized'])
        self.assertEqual(self.calls[0][1]['env']['INDEX_PATH'],str(self.state/'index.sqlite'))
    def test_missing_snapshot(self):
        self.assertEqual(self.run_search(indexed_hashes=None)['reason'],'index-snapshot-missing-or-stale');self.assertFalse(self.calls)
    def test_modified_source(self):
        (self.root/'a.md').write_text('new keyword', encoding='utf-8')
        self.assertEqual(self.run_search()['mode'],'literal');self.assertFalse(self.calls)
    def test_deleted_source(self):
        (self.root/'a.md').unlink();x=self.run_search();self.assertEqual(x['hits'],[]);self.assertEqual(x['unavailable'],['a.md'])
    def test_added_allowlist_source(self):
        (self.root/'b.md').write_text('keyword', encoding='utf-8')
        self.assertEqual(self.run_search(files=['a.md','b.md'])['mode'],'literal');self.assertFalse(self.calls)
    def test_failures(self):
        for error in [FileNotFoundError(),subprocess.CalledProcessError(1,'qmd'),subprocess.TimeoutExpired('qmd',10)]:
            def fail(*a,**k):raise error
            with self.subTest(error=type(error).__name__):
                x=self.run_search(runner=fail);self.assertEqual(x['mode'],'literal');self.assertEqual(len(x['hits']),1)
    def test_malformed_and_hostile_responses(self):
        for payload in ['not json','{}',json.dumps([{'file':'qmd://other/a.md','line':2}]),json.dumps([{'file':'qmd://authorized/../secret','line':1}]),json.dumps([{'file':'qmd://authorized/a.md','line':99}]),json.dumps([{'file':'qmd://authorized/a.md','line':True}])]:
            with self.subTest(payload=payload):self.assertEqual(self.run_search(runner=lambda *a,**k:SimpleNamespace(stdout=payload))['mode'],'literal')
    def test_empty_not_failure(self):
        x=self.run_search(runner=lambda *a,**k:SimpleNamespace(stdout='[]'));self.assertEqual(x['mode'],'qmd-keyword');self.assertEqual(x['hits'],[])
    def test_race_does_not_serve_old_source(self):
        def race(*a,**k):
            (self.root/'a.md').write_text('replacement keyword', encoding='utf-8')
            return self.runner(*a,**k)
        x=self.run_search(runner=race);self.assertEqual(x['mode'],'literal');self.assertIn('replacement',x['hits'][0]['text'])
    def test_symlink_rejected(self):
        (self.base/'outside').write_text('keyword', encoding='utf-8');(self.root/'a.md').unlink();
        try:
            (self.root/'a.md').symlink_to(self.base/'outside')
        except (OSError, NotImplementedError) as exc:
            self.skipTest('symlink creation unavailable: ' + str(exc))
        x=self.run_search();self.assertEqual(x['hits'],[]);self.assertFalse(self.calls)
    def test_state_in_vault_rejected(self):
        self.assertEqual(self.run_search(state_dir=self.root)['reason'],'unsafe-state-directory')
    def test_public_enable_cannot_execute(self):
        x=m.search('keyword', **self.args, enabled=True, runner=self.runner)
        self.assertEqual(x['reason'],'qmd-experimental-index-binding-unimplemented')
        self.assertEqual(x['mode'],'literal');self.assertFalse(self.calls)
    def test_public_literal_matches_before_loading_next_source(self):
        events = []
        class TracedText(str):
            def splitlines(self):
                events.append(('match', str(self)))
                return super().splitlines()
        def read(root, name):
            events.append(('read', name))
            return TracedText(name)
        with mock.patch.object(m, '_read', side_effect=read):
            result = m.search('not present', root=self.root, files=['a.md', 'b.md'])
        self.assertEqual(result['hits'], [])
        self.assertEqual(events, [('read', 'a.md'), ('match', 'a.md'),
                                  ('read', 'b.md'), ('match', 'b.md')])
    def test_public_literal_limit_preserves_late_unavailable(self):
        (self.root / 'invalid.md').write_bytes(b'\xff')
        (self.root / 'oversized.md').write_bytes(b'x' * (m.MAX_BYTES + 1))
        files = ['a.md', 'a.md', 'missing.md', 'invalid.md', 'oversized.md', '../outside']
        result = m.search('KEYWORD', root=self.root, files=files, limit=1,
                          enabled=True, runner=self.runner)
        self.assertEqual(result['reason'], 'qmd-experimental-index-binding-unimplemented')
        self.assertEqual(result['hits'], [{'file': 'a.md', 'line': 2,
                                         'text': '# Synthetic\n关键词 keyword'}])
        self.assertEqual(result['unavailable'], ['missing.md', 'invalid.md',
                                                'oversized.md', '../outside'])
        self.assertFalse(self.calls)
    def test_noninteger_limits_rejected_before_source_reads(self):
        # Numeric range comparisons alone accept floats and bools; a fractional
        # limit can never equal the integer hit count and silently bypass the cap.
        for limit in [1.5, 1.0, True, False, '5', None]:
            for enabled in [False, True]:
                with self.subTest(limit=repr(limit), enabled=enabled):
                    with mock.patch.object(m, '_read') as read:
                        with self.assertRaises(ValueError):
                            m.search('keyword', root=self.root, files=['a.md'],
                                     limit=limit, enabled=enabled, runner=self.runner)
                        read.assert_not_called()
        self.assertFalse(self.calls)

    def test_public_integer_limit_bounds_cap_all_matching_files(self):
        files = ['match-%d.md' % i for i in range(25)]
        for name in files:
            (self.root / name).write_text('keyword', encoding='utf-8')
        for limit in [1, 5, 20]:
            with self.subTest(limit=limit):
                result = m.search('keyword', root=self.root, files=files, limit=limit)
                self.assertEqual(len(result['hits']), limit)
                self.assertEqual([hit['file'] for hit in result['hits']], files[:limit])
        for limit in [0, 21, -1]:
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    m.search('keyword', root=self.root, files=files, limit=limit)

    def test_empty_result_mutation(self):
        def race(*a,**k):
            (self.root/'a.md').write_text('new keyword',encoding='utf-8')
            return SimpleNamespace(stdout='[]')
        x=self.run_search(runner=race)
        self.assertEqual(x['mode'],'literal');self.assertIn('new keyword',x['hits'][0]['text'])
    def test_non_hit_mutation_and_delete(self):
        b=self.root/'b.md';b.write_text('other',encoding='utf-8')
        args={'files':['a.md','b.md'],'indexed_hashes':{**self.args['indexed_hashes'], 'b.md':m._hash('other')}}
        for delete in [False,True]:
            b.write_text('other',encoding='utf-8')
            def race(*a,**k):
                if delete:b.unlink()
                else:b.write_text('changed keyword',encoding='utf-8')
                return self.runner(*a,**k)
            with self.subTest(delete=delete):self.assertEqual(self.run_search(runner=race,**args)['mode'],'literal')
    def test_invalid_utf8_source(self):
        (self.root/'a.md').write_bytes(b'\xff')
        self.assertEqual(self.run_search()['unavailable'],['a.md'])
    def test_bounded_runner(self):
        self.assertEqual(m._bounded_run([sys.executable,'-c',"import sys;sys.stdout.buffer.write('中文'.encode('utf-8'))"]).stdout,'中文')
        with self.assertRaises(ValueError):m._bounded_run([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'x'*1000000)"],max_bytes=1000)
        with self.assertRaises(UnicodeDecodeError):m._bounded_run([sys.executable,'-c',"import sys;sys.stdout.buffer.write(bytes([255]))"])
        with self.assertRaises(subprocess.TimeoutExpired):m._bounded_run([sys.executable,'-c','import time;time.sleep(2)'],timeout=0.1)
        with self.assertRaises(subprocess.CalledProcessError):m._bounded_run([sys.executable,'-c','raise SystemExit(1)'])
        self.assertEqual(m._bounded_run([sys.executable,'-c',"import sys;sys.stderr.buffer.write(b'x'*1000000);print('[]')"]).stdout.strip(),'[]')
    def test_crlf_hash_uses_actual_utf8_bytes(self):
        import hashlib
        raw='# Synthetic\r\n关键词 keyword\r\n'.encode('utf-8')
        (self.root/'a.md').write_bytes(raw)
        digest=m._hash(m._read(self.root,'a.md'))
        self.assertEqual(digest,hashlib.sha256(raw).hexdigest())
        x=self.run_search(indexed_hashes={'a.md':digest})
        self.assertEqual(x['mode'],'qmd-keyword')
        self.assertIn('关键词 keyword',x['hits'][0]['text'])
    def test_normalized_lf_hash_cannot_match_crlf_source(self):
        text='# Synthetic\r\n关键词 keyword\r\n'
        (self.root/'a.md').write_bytes(text.encode('utf-8'))
        x=self.run_search(indexed_hashes={'a.md':m._hash(text.replace('\r\n','\n'))})
        self.assertEqual(x['reason'],'index-snapshot-missing-or-stale')
        self.assertFalse(self.calls)
    def test_option_injection_rejected(self):
        with self.assertRaises(ValueError):m.search('--help',**self.args)

if __name__=='__main__':unittest.main()
