import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('safe_install', REPO / 'installers/safe-install.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InstallSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / 'repo'
        self.source = self.repo / 'skills/demo-skill'
        self.source.mkdir(parents=True)
        (self.repo / 'registry.yaml').write_text('skills:\n  - slug: demo-skill\n')
        (self.source / 'SKILL.md').write_text('v1')
        (self.source / 'references').mkdir()
        (self.source / 'references/canvas-state.md').write_text('example')
        self.root = self.base / 'skills space 中文'
        self.target = self.root / 'collection/demo-skill'

    def install(self, **kw):
        opts = dict(repo=self.repo, source=self.source, target=self.target,
                    root=self.root, skill='demo-skill', collection='collection')
        opts.update(kw)
        return mod.install(**opts)

    def test_dry_run_creates_nothing(self):
        before = mod.snapshot(self.base)
        self.install(dry_run=True)
        self.assertEqual(before, mod.snapshot(self.base))

    def test_fresh_install_and_reinstall_preserve_user_files_and_state(self):
        self.install()
        (self.target / 'notes.txt').write_text('mine')
        (self.target / 'references/canvas-state.md').write_text('current state')
        (self.source / 'SKILL.md').write_text('v2')
        self.install()
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'v2')
        self.assertEqual((self.target / 'notes.txt').read_text(), 'mine')
        self.assertEqual((self.target / 'references/canvas-state.md').read_text(), 'current state')
        backups = list((self.root.parent / '.nep7une-skill-backups').glob('demo-skill-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'SKILL.md').read_text(), 'v1')
        before = mod.snapshot(self.target)
        self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_local_mode_preserved_and_backup_outside_discovery_root(self):
        self.install()
        (self.target / 'SKILL.md').chmod(0o600)
        (self.source / 'SKILL.md').write_text('v2')
        self.install()
        self.assertEqual((self.target / 'SKILL.md').stat().st_mode & 0o777, 0o600)
        discovered = list(self.root.rglob('SKILL.md'))
        self.assertEqual(discovered, [self.target / 'SKILL.md'])

    def test_no_prune(self):
        self.install()
        (self.source / 'SKILL.md').write_text('v2')
        (self.source / 'references/canvas-state.md').unlink()
        self.install()
        self.assertTrue((self.target / 'references/canvas-state.md').exists())

    def test_existing_unowned_target_refused(self):
        self.target.mkdir(parents=True)
        (self.target / 'mine').write_text('keep')
        before = mod.snapshot(self.target)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_modified_managed_file_refused_without_change(self):
        self.install()
        (self.target / 'SKILL.md').write_text('local')
        (self.source / 'SKILL.md').write_text('upstream')
        before = mod.snapshot(self.target)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_unmanaged_collision_refused(self):
        self.install()
        (self.target / 'extra').write_text('local')
        (self.source / 'extra').write_text('upstream')
        before = mod.snapshot(self.target)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_dangerous_and_traversal_paths(self):
        for target in (Path('/'), Path.home(), self.repo, self.source, self.root):
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.install(target=target)
        for skill in ('../demo-skill', 'unknown', '/tmp/demo-skill'):
            with self.subTest(skill=skill), self.assertRaises(ValueError):
                self.install(skill=skill)
        with self.assertRaises(ValueError): self.install(collection='../escape')

    def test_symlink_destination_and_source_refused(self):
        self.root.mkdir()
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / 'collection').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(list(outside.iterdir()), [])
        (self.root / 'collection').unlink()
        (self.source / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.install()

    def test_target_file_symlink_refused(self):
        self.install()
        (self.target / 'link').symlink_to(self.source / 'SKILL.md')
        with self.assertRaises(ValueError): self.install()

    def test_mismatched_manifest(self):
        self.install()
        marker = self.target / mod.MARKER
        meta = json.loads(marker.read_text()); meta['skill'] = 'wrong'
        marker.write_text(json.dumps(meta))
        with self.assertRaises(ValueError): self.install()

    def test_failed_stage_preserves_original(self):
        self.install()
        before = mod.snapshot(self.target)
        with patch.object(mod.shutil, 'copy2', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_failed_swap_restores_original(self):
        self.install()
        before = mod.snapshot(self.target)
        real = os.rename
        def fail_stage(src, dst):
            if '.stage-' in str(src): raise OSError('injected rename failure')
            return real(src, dst)
        with patch.object(mod.os, 'rename', side_effect=fail_stage):
            with self.assertRaises(OSError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_concurrent_edit_detected_before_swap(self):
        self.install()
        real = mod.shutil.copytree
        def concurrent(*args, **kwargs):
            result = real(*args, **kwargs)
            (self.target / 'mine').write_text('concurrent edit')
            return result
        with patch.object(mod.shutil, 'copytree', side_effect=concurrent):
            with self.assertRaises(ValueError): self.install()
        self.assertEqual((self.target / 'mine').read_text(), 'concurrent edit')
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'v1')

    def test_lock_refuses_second_install(self):
        self.install()
        lock = self.target.with_name('.demo-skill.install-lock'); lock.mkdir()
        before = mod.snapshot(self.target)
        with self.assertRaises(FileExistsError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))
        self.assertTrue(lock.exists())

    def test_all_shell_entrypoints_use_safe_helper(self):
        for runtime in ('codex', 'hermes', 'openclaw'):
            with self.subTest(runtime=runtime):
                root = self.base / runtime
                cmd = ['bash', str(REPO / f'installers/install-{runtime}.sh'),
                       '--skill', 'server-ops-skill', '--skills-dir', str(root), '--skip-deps']
                result = subprocess.run(cmd + ['--dry-run'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(root.exists())
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((root / 'nep7une-skills/server-ops-skill' / mod.MARKER).exists())
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
