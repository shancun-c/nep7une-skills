"""End-to-end smoke tests for the public Bash installer entrypoints."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from process_helper import run as run_test_process


REPO = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
SKILL = 'knowledge-canvas-sync'
COLLECTION = 'nep7une-skills'


@unittest.skipIf(os.name == 'nt', 'native Windows Bash path interoperability is not covered')
@unittest.skipUnless(BASH and shutil.which('python3'), 'installer requires Bash and python3')
class PublicInstallerSmoke(unittest.TestCase):
    def test_install_and_reinstall_through_public_wrappers(self):
        for runtime in ('codex', 'hermes', 'openclaw'):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                if runtime == 'openclaw':
                    workspace = root / 'isolated workspace'
                    target = workspace / 'skills' / COLLECTION / SKILL
                    args = ['--target', str(workspace)]
                else:
                    skills_root = root / 'isolated skills root'
                    target = skills_root / 'explicit package parent' / SKILL
                    args = ['--skills-dir', str(skills_root), '--target', str(target)]

                sibling = target.parent / 'unrelated package'
                sibling.mkdir(parents=True)
                sentinel = sibling / 'keep.txt'
                sentinel.write_bytes(b'leave this alone\n')
                home = root / 'isolated home'
                env = {'PATH': os.environ.get('PATH', os.defpath), 'HOME': str(home),
                       'CODEX_HOME': str(root / 'codex home'),
                       'HERMES_HOME': str(root / 'hermes home')}
                command = [BASH, str(REPO / 'installers' / f'install-{runtime}.sh'),
                           *args, '--skill', SKILL, '--skip-deps']
                self.assertFalse(target.exists())
                marker_path = target / '.nep7une-install.json'
                initial_marker = None
                for expected in ('Installed', 'Already up to date'):
                    with self.subTest(step=expected):
                        result = run_test_process(command, cwd=root, env=env, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                        self.assertIn(f'{expected}: {target}', result.stdout.splitlines())
                        self.assertIn('Dependency check: skipped', result.stdout.splitlines())
                        raw_marker = marker_path.read_bytes()
                        marker = json.loads(raw_marker)
                        self.assertEqual((marker['schema'], marker['skill'], marker['collection']),
                                         (1, SKILL, COLLECTION))
                        for relative in ('SKILL.md', 'scripts/verify-canvas-colors.py'):
                            self.assertIn(relative, marker['files'])
                            self.assertEqual((target / relative).read_bytes(),
                                             (REPO / 'skills' / SKILL / relative).read_bytes())
                        self.assertEqual(list(sibling.iterdir()), [sentinel])
                        self.assertEqual(sentinel.read_bytes(), b'leave this alone\n')
                        if initial_marker is not None:
                            self.assertEqual(raw_marker, initial_marker)
                        initial_marker = raw_marker
