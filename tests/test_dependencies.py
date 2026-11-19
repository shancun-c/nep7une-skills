"""Dependency presence contracts, not external companion behavior certification."""
from pathlib import Path
import re
import subprocess
from process_helper import run as run_test_process
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = ('codex', 'hermes', 'openclaw')


class DependencyContracts(unittest.TestCase):
    def declared(self):
        # Parse only the registry's current constrained indentation/list format.
        result = {}
        skill = runtime = level = None
        in_deps = False
        for line in (ROOT / 'registry.yaml').read_text(encoding='utf-8').splitlines():
            match = re.fullmatch(r'  - slug: ([a-z0-9-]+)', line)
            if match:
                skill = match[1]; in_deps = False
            elif line == '    dependencies:':
                in_deps = True
            elif in_deps and re.match(r'    \S', line):
                in_deps = False
            elif in_deps:
                match = re.fullmatch(r'      (codex|hermes|openclaw):', line)
                if match:
                    runtime = match[1]
                    continue
                match = re.fullmatch(r'        (required|recommended|optional):(?: \[\])?', line)
                if match:
                    level = match[1]; result[skill, runtime, level] = []
                    continue
                match = re.fullmatch(r'          - ([a-z0-9-]+)', line)
                if match:
                    result[skill, runtime, level].append(match[1])
        return result

    def test_registry_structure_and_canvas_companion_declarations(self):
        declared = self.declared()
        self.assertEqual(len(declared), 27)
        for runtime in RUNTIMES:
            self.assertIn('obsidian-canvas-creator',
                          declared['knowledge-canvas-sync', runtime, 'required'])
            for level in ('required', 'recommended', 'optional'):
                self.assertNotIn('json-canvas',
                                 declared['knowledge-canvas-sync', runtime, level])

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_shell_registry_parity_all_skills_and_runtimes(self):
        declared = self.declared()
        self.assertEqual(len(declared), 27)
        for (skill, runtime, level), expected in declared.items():
            with self.subTest(skill=skill, runtime=runtime, level=level):
                r = run_test_process(['bash', '-c', '. "$1"; skill_dependencies "$2" "$3" "$4"',
                    '_', str(ROOT / 'installers/lib.sh'), runtime, skill, level],
                    capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.splitlines(), expected)

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_canvas_requires_creator_not_generic_canvas(self):
        declared = self.declared()
        for runtime in RUNTIMES:
            self.assertIn('obsidian-canvas-creator', declared['knowledge-canvas-sync', runtime, 'required'])
            for level in ('required', 'recommended', 'optional'):
                self.assertNotIn('json-canvas', declared['knowledge-canvas-sync', runtime, level])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'skills'
                # Generic canvas and the other requirements do not replace Creator.
                for dep in ('json-canvas', 'obsidian', 'obsidian-markdown'):
                    folder = root / dep; folder.mkdir(parents=True)
                    (folder / 'SKILL.md').write_text('---\nname: ' + dep + '\n---\n')
                cmd = ['bash', str(ROOT / f'installers/install-{runtime}.sh'),
                    '--skills-dir', str(root), '--skill', 'knowledge-canvas-sync']
                r = run_test_process(cmd, capture_output=True, text=True)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn('required missing: obsidian-canvas-creator', r.stderr)
                self.assertFalse((root / 'nep7une-skills').exists())
                creator = root / 'obsidian-canvas-creator'; creator.mkdir()
                (creator / 'SKILL.md').write_text('---\nname: obsidian-canvas-creator\n---\n')
                r = run_test_process(cmd, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn('optional missing:', r.stderr)
                self.assertTrue((root / 'nep7une-skills/knowledge-canvas-sync/SKILL.md').is_file())

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_aliased_canvas_companion_accepts_crlf_frontmatter(self):
        declared = self.declared()
        for runtime in RUNTIMES:
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'skills'
                for dep in declared['knowledge-canvas-sync', runtime, 'required']:
                    folder = root / 'scope' / ('alias-' + dep)
                    folder.mkdir(parents=True)
                    (folder / 'SKILL.md').write_bytes(
                        ('---\r\nname: ' + dep + '\r\n---\r\n').encode('utf-8'))
                r = run_test_process(['bash', str(ROOT / f'installers/install-{runtime}.sh'),
                    '--skills-dir', str(root), '--skill', 'knowledge-canvas-sync', '--dry-run'],
                    capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn('required ok: obsidian-canvas-creator', r.stdout)
                self.assertFalse((root / 'nep7une-skills').exists())

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_aliased_dependency_lookup_stays_inside_frontmatter(self):
        for eol in (b'\n', b'\r\n'):
            with self.subTest(eol=eol), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                alias = root / 'different-folder'
                alias.mkdir()
                cmd = ['bash', '-c', '. "$1"; skill_installed "$2" "$3"', '_',
                       str(ROOT / 'installers/lib.sh'), str(root), 'obsidian-canvas-creator']
                marker = alias / 'SKILL.md'
                marker.write_bytes(eol.join([b'---', b'description: example', b'---',
                                            b'name: obsidian-canvas-creator', b'']))
                r = run_test_process(cmd, capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, r.stderr)
                marker.write_bytes(eol.join([b'---', b'name: obsidian-canvas-creator', b'---', b'']))
                r = run_test_process(cmd, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipUnless(shutil.which('bash'), 'Bash executable is required for shell integration')
    def test_each_canvas_required_companion_is_enforced(self):
        declared = self.declared()
        for runtime in RUNTIMES:
            required = declared['knowledge-canvas-sync', runtime, 'required']
            for missing in required:
                with self.subTest(runtime=runtime, missing=missing), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp) / 'skills'
                    for dep in required:
                        if dep == missing:
                            continue
                        folder = root / dep; folder.mkdir(parents=True)
                        (folder / 'SKILL.md').write_text('---\nname: ' + dep + '\n---\n')
                    r = run_test_process(['bash', str(ROOT / f'installers/install-{runtime}.sh'),
                        '--skills-dir', str(root), '--skill', 'knowledge-canvas-sync'],
                        capture_output=True, text=True)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn('required missing: ' + missing, r.stderr)
                    self.assertFalse((root / 'nep7une-skills').exists())


if __name__ == '__main__':
    unittest.main()
