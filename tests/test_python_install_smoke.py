"""Native Python helper smoke tests; not shell/runtime integration certification."""
import json
from pathlib import Path
import subprocess
from process_helper import run as run_test_process
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class NativePythonInstallation(unittest.TestCase):
    def test_real_packages_install_and_reinstall_without_bash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'skills space'
            for skill in ('obsidian-wiki-skill', 'knowledge-canvas-sync', 'server-ops-skill'):
                with self.subTest(skill=skill):
                    target = root / 'nep7une-skills' / skill
                    command = [sys.executable, str(REPO / 'installers/safe-install.py'),
                               '--repo', str(REPO), '--source', str(REPO / 'skills' / skill),
                               '--target', str(target), '--root', str(root),
                               '--skill', skill, '--collection', 'nep7une-skills']
                    result = run_test_process(command + ['--dry-run'], capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(target.exists())
                    for _ in range(2):
                        result = run_test_process(command, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                    for source in (REPO / 'skills' / skill).rglob('*'):
                        if source.is_file() and '__pycache__' not in source.parts:
                            self.assertEqual(source.read_bytes(), (target / source.relative_to(
                                REPO / 'skills' / skill)).read_bytes())
                    marker = json.loads((target / '.nep7une-install.json').read_text(encoding='utf-8'))
                    self.assertEqual(marker['skill'], skill)

    def test_installed_canvas_cli_on_synthetic_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'skills'
            skill = 'knowledge-canvas-sync'
            target = root / 'nep7une-skills' / skill
            result = run_test_process([sys.executable, str(REPO / 'installers/safe-install.py'),
                '--repo', str(REPO), '--source', str(REPO / 'skills' / skill),
                '--target', str(target), '--root', str(root), '--skill', skill,
                '--collection', 'nep7une-skills'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            canvas = Path(tmp) / 'sample.canvas'
            canvas.write_text(json.dumps({'nodes': [{'id': 'g', 'type': 'group',
                'x': 0, 'y': 0, 'width': 100, 'height': 100, 'color': '5'}], 'edges': []}), encoding='utf-8')
            original = canvas.read_bytes()
            for script, flags in [('fix-canvas-colors.py', ['--dry-run']),
                                  ('fix-canvas-colors.py', []), ('verify-canvas-colors.py', [])]:
                result = run_test_process([sys.executable, str(target / 'scripts' / script),
                                         *flags, str(canvas)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                if flags:
                    self.assertEqual(canvas.read_bytes(), original)
            backups = list(canvas.parent.glob('sample.canvas.backup-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
