"""Synthetic batching limits and changes across the normalization boundary."""
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import test_qmd_generation as fixtures
from tools import qmd_generation as g


class MockBudgetTests(unittest.TestCase):
    def test_limits_fail_before_starting_process(self):
        rows = [(i,'synthetic','a.md','title','content') for i in range(4)]
        cases = [('NORMALIZER_MAX_ROWS', 3), ('NORMALIZER_TOTAL_BYTES', 50),
                 ('NORMALIZER_BATCH_BYTES', 10), ('NORMALIZER_MAX_BATCHES', 0)]
        for constant, value in cases:
            with self.subTest(constant=constant), patch.object(g,constant,value), patch.object(g,'_bounded_run') as run:
                with self.assertRaises(ValueError):g._normalize_rows(rows, Path('unused'))
                run.assert_not_called()

    def test_cumulative_output_and_deadline(self):
        rows = [(1,'synthetic','a.md','title','content')]
        with patch.object(g,'NORMALIZER_TOTAL_OUTPUT_BYTES',2), patch.object(g,'_bounded_run',return_value=SimpleNamespace(stdout='["a","b","c"]')):
            with self.assertRaisesRegex(ValueError,'cumulative output'):g._normalize_rows(rows,Path('unused'))
        with patch.object(g,'NORMALIZER_SECONDS',0), patch.object(g,'_bounded_run') as run:
            with self.assertRaisesRegex(ValueError,'deadline'):g._normalize_rows(rows,Path('unused'))
            run.assert_not_called()


    def test_malformed_responses_are_rejected(self):
        rows = [(1, 'synthetic', 'a.md', 'title', 'content')]
        outputs = ['not json', 'null', '{}', '1', '"abc"',
                   '["a", "b"]', '["a", "b", "c", "d"]', '["a", 1, "c"]']
        for output in outputs:
            with self.subTest(output=output), patch.object(
                    g, '_bounded_run', return_value=SimpleNamespace(stdout=output)):
                with self.assertRaises(ValueError):
                    g._normalize_rows(rows, Path('unused'))

    def test_multibatch_allowances_decrease(self):
        rows = [(i, 'synthetic', '%s.md' % i, 'title', 'content') for i in range(2)]
        observed = []
        def respond(argv, **kwargs):
            payload = Path(argv[-1]).read_text(encoding='utf-8')
            observed.append((kwargs, payload))
            return SimpleNamespace(stdout=payload)
        with patch.object(g, 'NORMALIZER_BATCH_BYTES', 65), \
                patch.object(g, 'NORMALIZER_TOTAL_OUTPUT_BYTES', 100), \
                patch.object(g.time, 'monotonic', side_effect=[0, 1, 2, 3, 4]), \
                patch.object(g, '_bounded_run', side_effect=respond):
            result = g._normalize_rows(rows, Path('unused'))
        self.assertEqual(result, [value for row in rows for value in
                                 [row[1]+'/'+row[2], row[3], row[4]]])
        self.assertEqual(len(observed), 2)
        first_bytes = len(observed[0][1].encode('utf-8'))
        self.assertEqual(observed[0][0], {'timeout': 9, 'max_bytes': 100})
        self.assertEqual(observed[1][0], {'timeout': 7, 'max_bytes': 100-first_bytes})

    def test_expired_deadline_does_not_start_next_batch(self):
        rows = [(i, 'synthetic', '%s.md' % i, 'title', 'content') for i in range(2)]
        def respond(argv, **kwargs):
            return SimpleNamespace(stdout=Path(argv[-1]).read_text(encoding='utf-8'))
        with patch.object(g, 'NORMALIZER_BATCH_BYTES', 65), \
                patch.object(g.time, 'monotonic', side_effect=[0, 1, 9, 10]), \
                patch.object(g, '_bounded_run', side_effect=respond) as run:
            with self.assertRaisesRegex(ValueError, 'deadline'):
                g._normalize_rows(rows, Path('unused'))
        self.assertEqual(run.call_count, 1)

    def test_cumulative_output_rejects_later_batch(self):
        rows = [(i, 'synthetic', '%s.md' % i, 'title', 'content') for i in range(2)]
        observed = []
        def respond(argv, **kwargs):
            observed.append(kwargs)
            return SimpleNamespace(stdout=Path(argv[-1]).read_text(encoding='utf-8'))
        with patch.object(g, 'NORMALIZER_BATCH_BYTES', 65), \
                patch.object(g, 'NORMALIZER_TOTAL_OUTPUT_BYTES', 65), \
                patch.object(g, '_bounded_run', side_effect=respond):
            with self.assertRaisesRegex(ValueError, 'cumulative output'):
                g._normalize_rows(rows, Path('unused'))
        self.assertEqual(len(observed), 2)
        self.assertGreater(observed[0]['max_bytes'], observed[1]['max_bytes'])


@unittest.skipUnless(shutil.which('node'), 'existing Node required')
class BatchTests(unittest.TestCase):
    setUp = fixtures.GenerationTests.setUp

    def test_multiple_batches_equal_single_batch(self):
        rows = [(i,'synthetic','%s.md'%i,'中文','合成 keyword') for i in range(5)]
        expected = g._normalize_rows(rows, Path(shutil.which('node')))
        with patch.object(g, 'NORMALIZER_BATCH_BYTES', 65):
            self.assertEqual(g._normalize_rows(rows, Path(shutil.which('node'))), expected)

    def test_source_change_during_normalization_rejected(self):
        original = g._bounded_run
        for folder in [self.root, Path(self.m['staging_root'])]:
            def mutate(argv, **kwargs):
                result = original(argv, **kwargs)
                (folder/'a.md').write_bytes(b'changed after initial validation')
                return result
            with self.subTest(folder=folder), patch.object(g,'_bounded_run',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'source changed during FTS check'):
                    g.verify_fts(self.m, Path(shutil.which('node')))
            (folder/'a.md').write_bytes('中文 keyword'.encode('utf-8'))

    def test_batch_result_substitution_rejected(self):
        original = g._bounded_run
        def substitute(argv, **kwargs):
            result = original(argv, **kwargs)
            items = json.loads(result.stdout);items[-1] = 'substitution'
            return SimpleNamespace(stdout=json.dumps(items))
        with patch.object(g,'_bounded_run',side_effect=substitute):
            with self.assertRaisesRegex(ValueError,'FTS normalized'):
                g.verify_fts(self.m, Path(shutil.which('node')))

    def test_second_batch_tamper_and_first_source_race(self):
        import sqlite3
        from contextlib import closing
        from tools.qmd_index_experiment import identity
        from tools.qmd_keyword import _hash
        body = '中文 keyword'
        for folder in [self.root, Path(self.m['staging_root'])]:
            (folder/'b.md').write_bytes(body.encode('utf-8'))
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute('INSERT INTO documents VALUES (2,?,?,?,?,1)', ('synthetic','b.md','中文',_hash(body)))
            db.execute('INSERT INTO documents_fts(rowid,filepath,title,body) VALUES (2,?,?,?)', ('synthetic/b.md',' 中 文 ',' 中 文  keyword'))
        self.m['index'] = identity(self.index)
        self.m['sources']['b.md'] = _hash(body)
        original = g._bounded_run
        for mode in ['substitute', 'source-race']:
            calls = []
            def intercept(argv, **kwargs):
                result = original(argv, **kwargs)
                calls.append(1)
                if len(calls) == 2:
                    if mode == 'substitute':
                        items = json.loads(result.stdout); items[-1] = 'tampered'
                        return SimpleNamespace(stdout=json.dumps(items))
                    (self.root/'a.md').write_bytes(b'changed in later batch')
                return result
            with patch.object(g,'NORMALIZER_BATCH_BYTES',65), patch.object(g,'_bounded_run',side_effect=intercept):
                with self.assertRaises(ValueError):g.verify_fts(self.m,Path(shutil.which('node')))
            self.assertEqual(len(calls),2)
            (self.root/'a.md').write_bytes(body.encode('utf-8'))
