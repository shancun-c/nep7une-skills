"""Synthetic source races; no actual vault or QMD executable is used."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from tools import qmd_keyword as m


class SourceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'root'
        self.root.mkdir()
        self.parent = self.root / 'folder'
        self.parent.mkdir()
        self.source = self.parent / 'a.md'
        self.source.write_text('keyword original', encoding='utf-8')
        self.outside = self.base / 'outside'
        self.outside.mkdir()
        (self.outside / 'a.md').write_text('keyword OUTSIDE_SCOPE', encoding='utf-8')

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows symlink privilege unavailable')
            raise

    def search(self):
        return m.search('keyword', root=self.root, files=['folder/a.md'])

    def assert_unavailable(self, result):
        self.assertEqual(result['hits'], [])
        self.assertEqual(result['unavailable'], ['folder/a.md'])
        self.assertNotIn('OUTSIDE_SCOPE', str(result))

    def run_open_swap(self, change):
        original = os.open
        def swapped(path, *args, **kwargs):
            if Path(path) == self.source:
                change()
            return original(path, *args, **kwargs)
        with mock.patch.object(m.os, 'open', swapped):
            self.assert_unavailable(self.search())

    def test_leaf_symlink_swap(self):
        def change():
            self.source.unlink()
            self.symlink(self.source, self.outside / 'a.md')
        self.run_open_swap(change)

    def test_parent_symlink_swap(self):
        def change():
            self.parent.rename(self.root / 'old-folder')
            self.symlink(self.parent, self.outside, directory=True)
        self.run_open_swap(change)

    def test_regular_file_replacement(self):
        replacement = self.base / 'replacement'
        replacement.write_text('keyword replacement', encoding='utf-8')
        self.run_open_swap(lambda: os.replace(replacement, self.source))

    def test_parent_regular_directory_replacement(self):
        def change():
            self.parent.rename(self.root / 'old-folder')
            self.parent.mkdir()
            self.source.write_text('keyword replacement', encoding='utf-8')
        self.run_open_swap(change)

    def test_change_during_read(self):
        original = os.fdopen
        source = self.source
        class Reader:
            def __init__(self, f): self.f = f
            def __enter__(self): return self
            def __exit__(self, *args): self.f.close()
            def fileno(self): return self.f.fileno()
            def read(self, size):
                result = self.f.read(size)
                source.write_text('keyword changed and longer', encoding='utf-8')
                return result
        with mock.patch.object(m.os, 'fdopen', lambda *a, **k: Reader(original(*a, **k))):
            self.assert_unavailable(self.search())

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO only')
    def test_fifo_swap_does_not_block(self):
        def change():
            self.source.unlink()
            os.mkfifo(self.source)
        self.run_open_swap(change)

    def test_unchanged_source(self):
        self.assertEqual(self.search()['hits'][0]['text'], 'keyword original')
