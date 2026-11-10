"""Identity checks use synthetic regular files and never open special devices."""
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import qmd_index_experiment as q


class IdentityLimits(unittest.TestCase):
    def test_nonregular_identity_refuses_before_open(self):
        for mode in (stat.S_IFIFO, stat.S_IFDIR, stat.S_IFSOCK,
                     stat.S_IFCHR, stat.S_IFBLK):
            with self.subTest(mode=mode), \
                    patch.object(Path, 'is_symlink', return_value=False), \
                    patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=mode)), \
                    patch.object(Path, 'open') as opened:
                with self.assertRaisesRegex(ValueError, 'regular file'):
                    q.identity(Path('synthetic-special-file'))
                opened.assert_not_called()

    def test_exact_size_limit_keeps_identity_and_rejects_larger_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input'
            path.write_bytes(b'12345678')
            self.assertEqual(q.identity(path, max_bytes=8), q.identity(path))
            with patch.object(Path, 'open') as opened:
                with self.assertRaisesRegex(ValueError, 'byte budget'):
                    q.identity(path, max_bytes=7)
                opened.assert_not_called()

    def test_index_limit_applies_before_manifest_identity_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.sqlite'
            path.write_bytes(b'123456789')
            manifest = {'index': {'path': str(path)}}
            with patch.object(q, 'INDEX_MAX_BYTES', 8), patch.object(Path, 'open') as opened:
                with self.assertRaisesRegex(ValueError, 'byte budget'):
                    with q.checked_index_snapshot(manifest):
                        self.fail('oversized index was yielded')
                opened.assert_not_called()

    def test_replacement_between_stat_and_open_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, replacement = Path(tmp) / 'input', Path(tmp) / 'replacement'
            path.write_bytes(b'original')
            replacement.write_bytes(b'replaced')
            original_open = Path.open
            def replace_then_open(target, *args, **kwargs):
                os.replace(replacement, path)
                return original_open(target, *args, **kwargs)
            with patch.object(Path, 'open', replace_then_open):
                with self.assertRaisesRegex(ValueError, 'changed before inspection'):
                    q.identity(path)

    def test_growth_during_read_stops_at_one_byte_over_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input'
            path.write_bytes(b'12345678')
            original_open = Path.open
            read_sizes = []
            class GrowingReader:
                def __init__(self, handle):
                    self.handle = handle
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    self.handle.close()
                def fileno(self):
                    return self.handle.fileno()
                def read(self, size):
                    read_sizes.append(size)
                    if len(read_sizes) == 1:
                        with original_open(path, 'ab') as writer:
                            writer.write(b'x' * 100)
                    return self.handle.read(size)
            def growing_open(target, *args, **kwargs):
                return GrowingReader(original_open(target, *args, **kwargs))
            with patch.object(Path, 'open', growing_open):
                with self.assertRaisesRegex(ValueError, 'byte budget'):
                    q.identity(path, max_bytes=8)
            self.assertEqual(read_sizes, [9])

    def test_windows_ctime_semantics_keep_same_source_mutation_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input'
            path.write_bytes(b'content')
            baseline = path.stat()
            names = ('st_mode', 'st_dev', 'st_ino', 'st_size',
                     'st_mtime_ns', 'st_ctime_ns')
            def snapshot(ctime):
                values = {name: getattr(baseline, name) for name in names}
                values.update(st_ctime_ns=ctime, st_birthtime_ns=100)
                return SimpleNamespace(**values)
            # Path stat reports creation time; fstat reports change time.
            for path_changed, descriptor_changed, birth_changed in (
                    (False, False, False), (True, False, False),
                    (False, True, False), (False, False, True)):
                opened = snapshot(200)
                if birth_changed:
                    opened.st_birthtime_ns += 1
                with self.subTest(path_changed=path_changed,
                                  descriptor_changed=descriptor_changed), \
                        patch.object(q, 'os', SimpleNamespace(name='nt')), \
                        patch.object(Path, 'stat', side_effect=[snapshot(100),
                            snapshot(101 if path_changed else 100)]), \
                        patch.object(Path, 'is_symlink', return_value=False), \
                        patch.object(Path, 'resolve', return_value=path), \
                        patch.object(q.os, 'fstat', create=True, side_effect=[opened,
                            snapshot(201 if descriptor_changed else 200)]):
                    if birth_changed:
                        with self.assertRaisesRegex(ValueError, 'changed before'):
                            q.identity(path)
                    elif path_changed or descriptor_changed:
                        with self.assertRaisesRegex(ValueError, 'changed during'):
                            q.identity(path)
                    else:
                        self.assertEqual(q.identity(path)['sha256'],
                                         hashlib.sha256(b'content').hexdigest())

    def test_empty_file_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'empty'
            path.write_bytes(b'')
            self.assertEqual(q.identity(path, max_bytes=0)['sha256'],
                             hashlib.sha256(b'').hexdigest())
            for limit in (-1, True, 1.5, '8'):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    q.identity(path, max_bytes=limit)


if __name__ == '__main__':
    unittest.main()
