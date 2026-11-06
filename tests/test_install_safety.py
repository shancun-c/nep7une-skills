import importlib.util
import json
import os
from pathlib import Path
import subprocess
from process_helper import run as run_test_process
import shutil
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

    def test_unchanged_reinstall_does_not_swap_or_create_backup(self):
        self.install()
        (self.target / 'notes.txt').write_text('user notes')
        (self.target / 'references/canvas-state.md').write_text('mutable state')
        before = mod.snapshot(self.target)
        marker = self.target / mod.MARKER
        marker_stat = marker.stat()
        with patch.object(mod.os, 'rename', side_effect=AssertionError('unexpected swap')):
            self.install()
            self.install()
        self.assertEqual(before, mod.snapshot(self.target))
        self.assertEqual(marker.stat().st_mtime_ns, marker_stat.st_mtime_ns)
        self.assertFalse((self.root.parent / '.nep7une-skill-backups').exists())
        self.assertFalse(self.target.with_name('.demo-skill.install-lock').exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX permission bits are not supported on Windows')
    def test_permission_only_edit_remains_noop(self):
        self.install()
        (self.target / 'SKILL.md').chmod(0o600)
        with patch.object(mod.os, 'rename', side_effect=AssertionError('unexpected swap')):
            self.install()
        self.assertEqual((self.target / 'SKILL.md').stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.root.parent / '.nep7une-skill-backups').exists())

    def test_missing_managed_file_is_restored(self):
        self.install()
        (self.target / 'SKILL.md').unlink()
        self.install()
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'v1')
        self.assertEqual(len(list((self.root.parent / '.nep7une-skill-backups')
                                 .glob('demo-skill-*'))), 1)

    def test_noop_rechecks_target_after_planning(self):
        self.install()
        original_validate = mod.validate
        calls = 0
        def changed_after_planning(*args, **kwargs):
            nonlocal calls
            original_validate(*args, **kwargs)
            calls += 1
            if calls == 2:
                (self.target / 'SKILL.md').write_text('concurrent user edit')
        with patch.object(mod, 'validate', side_effect=changed_after_planning):
            with self.assertRaisesRegex(ValueError, 'changed during planning'):
                self.install()
        self.assertEqual((self.target / 'SKILL.md').read_text(), 'concurrent user edit')
        self.assertFalse((self.root.parent / '.nep7une-skill-backups').exists())

    def test_new_package_file_still_updates_and_backs_up(self):
        self.install()
        (self.source / 'new.txt').write_text('new package file')
        self.install()
        self.assertEqual((self.target / 'new.txt').read_text(), 'new package file')
        backups = list((self.root.parent / '.nep7une-skill-backups').glob('demo-skill-*'))
        self.assertEqual(len(backups), 1)
        self.assertFalse((backups[0] / 'new.txt').exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX permission bits are not supported on Windows')
    def test_local_mode_preserved(self):
        self.install()
        (self.target / 'SKILL.md').chmod(0o600)
        (self.source / 'SKILL.md').write_text('v2')
        self.install()
        self.assertEqual((self.target / 'SKILL.md').stat().st_mode & 0o777, 0o600)

    def test_backup_outside_discovery_root(self):
        self.install()
        (self.source / 'SKILL.md').write_text('v2')
        self.install()
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

    def make_symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows symlink creation privilege unavailable')
            raise

    def test_symlink_destination_and_source_refused(self):
        self.root.mkdir()
        outside = self.base / 'outside'
        outside.mkdir()
        self.make_symlink(self.root / 'collection', outside, directory=True)
        with self.assertRaises(ValueError): self.install()
        self.assertEqual(list(outside.iterdir()), [])
        (self.root / 'collection').unlink()
        self.make_symlink(self.source / 'linked', outside, directory=True)
        with self.assertRaises(ValueError): self.install()

    def test_target_file_symlink_refused(self):
        self.install()
        self.make_symlink(self.target / 'link', self.source / 'SKILL.md')
        with self.assertRaises(ValueError): self.install()

    def test_mismatched_manifest(self):
        self.install()
        marker = self.target / mod.MARKER
        meta = json.loads(marker.read_text()); meta['skill'] = 'wrong'
        marker.write_text(json.dumps(meta))
        with self.assertRaises(ValueError): self.install()

    def test_failed_stage_preserves_original(self):
        self.install()
        (self.source / 'SKILL.md').write_text('v2')
        before = mod.snapshot(self.target)
        with patch.object(mod.shutil, 'copy2', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.install()
        self.assertEqual(before, mod.snapshot(self.target))

    def test_failed_swap_restores_original(self):
        self.install()
        (self.source / 'SKILL.md').write_text('v2')
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
        (self.source / 'SKILL.md').write_text('v2')
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

    def test_utf8_manifest_and_registry_ignore_locale(self):
        # Ensure required file reads choose UTF-8 even under non-UTF-8 locales.
        original_read = Path.read_text
        def strict_read(path, *args, **kwargs):
            if path.name in ('registry.yaml', mod.MARKER):
                self.assertEqual(kwargs.get('encoding'), 'utf-8')
            return original_read(path, *args, **kwargs)
        (self.repo / 'registry.yaml').write_text(
            '# 中文注册表\nskills:\n  - slug: demo-skill\n', encoding='utf-8')
        with patch.object(Path, 'read_text', strict_read):
            self.install()
            self.install()

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_missing_required_dependency_refuses_without_target(self):
        for runtime in ('codex', 'hermes', 'openclaw'):
            with self.subTest(runtime=runtime):
                root = self.base / runtime
                result = run_test_process(['bash', str(REPO / f'installers/install-{runtime}.sh'),
                    '--skills-dir', str(root)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Missing required skill dependencies', result.stderr)
                self.assertFalse(root.exists())

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_all_real_packages_roundtrip_and_installed_canvas_cli(self):
        import sys
        deps = ('obsidian', 'obsidian-markdown', 'obsidian-cli', 'obsidian-bases',
                'json-canvas', 'defuddle', 'anysearch', 'obsidian-canvas-creator')
        for runtime in ('codex', 'hermes', 'openclaw'):
            root = self.base / runtime
            for dep in deps:
                folder = root / dep
                folder.mkdir(parents=True)
                (folder / 'SKILL.md').write_text('---\nname: ' + dep + '\n---\n')
            for skill in ('obsidian-wiki-skill', 'knowledge-canvas-sync', 'server-ops-skill'):
                with self.subTest(runtime=runtime, skill=skill):
                    cmd = ['bash', str(REPO / f'installers/install-{runtime}.sh'),
                           '--skill', skill, '--skills-dir', str(root)]
                    for _ in range(2):
                        result = run_test_process(cmd, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                    installed = root / 'nep7une-skills' / skill
                    for source in (REPO / 'skills' / skill).rglob('*'):
                        if source.is_file() and '__pycache__' not in source.parts:
                            self.assertEqual(source.read_bytes(),
                                (installed / source.relative_to(REPO / 'skills' / skill)).read_bytes())
            scripts = root / 'nep7une-skills/knowledge-canvas-sync/scripts'
            canvas = self.base / (runtime + '.canvas')
            canvas.write_text(json.dumps({'nodes': [{'id': 'g', 'type': 'group',
                'x': 0, 'y': 0, 'width': 100, 'height': 100, 'color': '5'}], 'edges': []}))
            original = canvas.read_bytes()
            for script, args in [('fix-canvas-colors.py', ['--dry-run']),
                                 ('fix-canvas-colors.py', []),
                                 ('verify-canvas-colors.py', [])]:
                result = run_test_process([sys.executable, str(scripts / script), *args, str(canvas)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                if args:
                    self.assertEqual(canvas.read_bytes(), original)
            self.assertEqual(len(list(self.base.glob(runtime + '.canvas.backup-*'))), 1)

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_all_shell_entrypoints_use_safe_helper(self):
        for runtime in ('codex', 'hermes', 'openclaw'):
            with self.subTest(runtime=runtime):
                root = self.base / runtime
                cmd = ['bash', str(REPO / f'installers/install-{runtime}.sh'),
                       '--skill', 'server-ops-skill', '--skills-dir', str(root), '--skip-deps']
                result = run_test_process(cmd + ['--dry-run'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(root.exists())
                result = run_test_process(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((root / 'nep7une-skills/server-ops-skill' / mod.MARKER).exists())
                result = run_test_process(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
