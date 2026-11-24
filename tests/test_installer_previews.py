"""Public Bash target resolution without writing to any runtime."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from process_helper import run as run_test_process


ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = ('codex', 'hermes', 'openclaw')
SKILLS = ('knowledge-canvas-sync', 'obsidian-wiki-skill', 'server-ops-skill')


@unittest.skipIf(os.name == 'nt', 'native Windows Bash path interoperability is not covered')
@unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for installer previews')
class InstallerTargetPreviews(unittest.TestCase):
    def test_explicit_skills_root(self):
        for runtime in RUNTIMES:
            for skill in SKILLS:
                with self.subTest(runtime=runtime, skill=skill), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp).resolve()
                    skills_root = root / '技能 root'
                    target = skills_root / 'nep7une-skills' / skill
                    self.preview(runtime, skill, ['--skills-dir', str(skills_root)], root, target)

    def test_explicit_target_override(self):
        for runtime in RUNTIMES:
            for skill in SKILLS:
                with self.subTest(runtime=runtime, skill=skill), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp).resolve()
                    if runtime == 'openclaw':
                        workspace = root / '工作 workspace'
                        target = workspace / 'skills' / 'nep7une-skills' / skill
                        args = ['--target', str(workspace)]
                    else:
                        skills_root = root / '技能 root'
                        target = skills_root / 'different namespace' / skill
                        args = ['--skills-dir', str(skills_root), '--target', str(target)]
                    self.preview(runtime, skill, args, root, target)

    def test_missing_value_cannot_consume_dry_run(self):
        for runtime in RUNTIMES:
            for option in ('--target', '--skills-dir'):
                with self.subTest(runtime=runtime, option=option), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp).resolve()
                    target = root / 'destination'
                    if option == '--target' and runtime != 'openclaw':
                        target /= 'obsidian-wiki-skill'
                    env = dict(os.environ, HOME=str(root / 'home'),
                               CODEX_HOME=str(root / 'codex-home'),
                               HERMES_HOME=str(root / 'hermes-home'))
                    result = run_test_process(
                        ['bash', str(ROOT / 'installers' / f'install-{runtime}.sh'),
                         option, '--dry-run', option, str(target), '--skip-deps'],
                        capture_output=True, text=True, encoding='utf-8', env=env, cwd=root,
                    )
                    self.assertEqual(list(root.iterdir()), [], result.stdout + result.stderr)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(f'Missing value for {option}', result.stderr)

    def test_dash_prefixed_path_with_explicit_relative_prefix(self):
        for runtime in RUNTIMES:
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                env = dict(os.environ, HOME=str(root / 'home'),
                           CODEX_HOME=str(root / 'codex-home'),
                           HERMES_HOME=str(root / 'hermes-home'))
                result = run_test_process(
                    ['bash', str(ROOT / 'installers' / f'install-{runtime}.sh'),
                     '--skills-dir', './-skills', '--skip-deps', '--dry-run'],
                    capture_output=True, text=True, encoding='utf-8', env=env, cwd=root,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('Dry run: no files, locks or directories written.', result.stdout)
                self.assertEqual(list(root.iterdir()), [])

    def preview(self, runtime, skill, args, temporary_parent, target):
        env = dict(os.environ, HOME=str(temporary_parent / 'home'),
                   CODEX_HOME=str(temporary_parent / 'codex-home'),
                   HERMES_HOME=str(temporary_parent / 'hermes-home'))
        result = run_test_process(
            ['bash', str(ROOT / 'installers' / f'install-{runtime}.sh'),
             *args, '--skill', skill, '--skip-deps', '--dry-run'],
            capture_output=True, text=True, encoding='utf-8', env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        reported = [Path(line[len('Target:  '):]) for line in result.stdout.splitlines()
                    if line.startswith('Target:  ')]
        self.assertEqual(reported, [target])
        self.assertIn('Dry run: no files, locks or directories written.', result.stdout)
        self.assertEqual(list(temporary_parent.iterdir()), [])
