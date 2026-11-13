import importlib.util
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('safe_install_reparse', REPO / 'installers/safe-install.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ReparseGuards(unittest.TestCase):
    def test_reparse_attribute_is_rejected_without_following(self):
        value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0x400)
        with patch.object(Path, 'lstat', return_value=value):
            with self.assertRaises(ValueError):
                mod.checked_lstat(Path('synthetic'))

    def test_regular_attribute_is_allowed(self):
        value = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_file_attributes=0x20)
        with patch.object(Path, 'lstat', return_value=value):
            self.assertIs(mod.checked_lstat(Path('synthetic')), value)

    def test_snapshot_refuses_directory_before_descent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / 'child'
            child.mkdir()
            original_stat, original_iter = Path.lstat, Path.iterdir
            def checked(path):
                value = original_stat(path)
                if path == child:
                    return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
                return value
            def listing(path):
                self.assertNotEqual(path, child, 'must refuse before descending')
                return original_iter(path)
            with patch.object(Path, 'lstat', checked), patch.object(Path, 'iterdir', listing):
                with self.assertRaises(ValueError):
                    mod.snapshot(root)

    @unittest.skipUnless(os.name == 'nt', 'Windows junction semantics')
    def test_native_junction_parent_and_tree_refused_before_install(self):
        import _winapi
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            actual = base / 'actual'
            actual.mkdir()
            alias = base / 'alias'
            _winapi.CreateJunction(str(actual), str(alias))
            try:
                with self.assertRaises(ValueError):
                    mod.no_symlinks(alias / 'missing' / 'demo-skill')
                with self.assertRaises(ValueError):
                    mod.snapshot(base)
                repo = base / 'repo'
                source = repo / 'skills' / 'demo-skill'
                source.mkdir(parents=True)
                (source / 'SKILL.md').write_text('synthetic', encoding='utf-8')
                (repo / 'registry.yaml').write_text('skills:\n  - slug: demo-skill\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    mod.install(repo, source, alias / 'collection' / 'demo-skill',
                                alias, 'demo-skill', 'collection')
                self.assertEqual(list(actual.iterdir()), [])
            finally:
                # Remove only the known junction itself, never its referent.
                os.rmdir(alias)


if __name__ == '__main__':
    unittest.main()
