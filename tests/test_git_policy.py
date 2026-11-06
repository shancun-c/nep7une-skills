"""Policy regression checks and a disposable local Git safety demonstration.

The fixture proves ordinary Git behavior, not agent compliance with prose.
No network, user vault, credentials, or real remote is used.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
from process_helper import run as run_test_process
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'obsidian-wiki-skill'


class GitPolicyDocuments(unittest.TestCase):
    def test_all_active_publication_routes_are_opt_in(self):
        for filename in ['SKILL.md', 'references/two-step-ingest.md',
                         'references/workflow-modes.md', 'references/vault-config.md',
                         'references/git-sync-pitfalls.md']:
            with self.subTest(filename=filename):
                text = (SKILL / filename).read_text(encoding='utf-8')
                self.assertIn('Local editing does not authorize publication', text)
                self.assertIn('branch', text)

    def test_no_dangerous_executable_recipe(self):
        for p in SKILL.rglob('*.md'):
            text = p.read_text(encoding='utf-8')
            code = '\n'.join(re.findall(r'```(?:bash|sh)?\n(.*?)```', text, re.S))
            self.assertNotRegex(code, r'git\s+(?:init|reset|add\s+-A)\b')
            self.assertNotRegex(code, r'git[^\n]*push[^\n]*(?:--force|\s-f\b)')
            self.assertNotRegex(code, r'rsync[^\n]*--delete')

    def test_no_personal_fallback(self):
        text = (SKILL / 'references/vault-config.md').read_text(encoding='utf-8')
        for private_value in ['wenweikun', '/Users/nep7une', 'the_ai_obsidian']:
            self.assertNotIn(private_value, text)
        self.assertIn('There is no fallback remote or branch', text)

    def test_remote_preservation_and_stop_conditions_are_required(self):
        text = (SKILL / 'references/git-sync-pitfalls.md').read_text(encoding='utf-8')
        for invariant in ['remote-only', 'allowlist', 'all push URLs',
                          'ahead, behind, or diverged', 'ordinary fast-forward push',
                          'Read back the remote tip', 'not an automatic sync implementation']:
            self.assertIn(invariant, text)


@unittest.skipUnless(shutil.which('git'), 'Git not installed')
class DisposableGitBehavior(unittest.TestCase):
    def test_allowlisted_update_preserves_remote_and_rejects_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = dict(os.environ, HOME=tmp, GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')

            def git(*args, cwd=None, ok=True, text=True):
                r = run_test_process(['git', '-c', 'user.name=Fixture', '-c',
                                    'user.email=fixture@example.invalid', '-c', 'core.autocrlf=false', *args],
                                   cwd=cwd, env=env, capture_output=True, text=text)
                if ok:
                    self.assertEqual(r.returncode, 0, r.stderr)
                return r

            remote, seed, checkout, other = [root / x for x in
                                             ('remote.git', 'seed', 'checkout', 'other')]
            git('init', '--bare', '--initial-branch=main', str(remote))
            git('clone', str(remote), str(seed))
            # Exact bytes: neither platform text I/O nor Git EOL conversion may
            # weaken the preservation check. -c options affect fixture commands only.
            preserved = b'must survive\n'
            concurrent = b'concurrent content\n'
            approved = b'approved update\n'
            (seed / 'remote-only.md').write_bytes(preserved)
            (seed / 'approved.md').write_bytes(b'baseline\n')
            git('add', '--', 'remote-only.md', 'approved.md', cwd=seed)
            git('commit', '-m', 'baseline', cwd=seed)
            git('push', 'origin', 'HEAD:refs/heads/main', cwd=seed)
            git('clone', str(remote), str(checkout))
            git('clone', str(remote), str(other))
            (checkout / 'approved.md').write_bytes(approved)
            git('add', '--', 'approved.md', cwd=checkout)
            staged = git('diff', '--cached', '--name-only', cwd=checkout).stdout.splitlines()
            self.assertEqual(staged, ['approved.md'])
            git('commit', '-m', 'local approved update', cwd=checkout)
            # Simulate a race after the pre-push fetch/check.
            (other / 'new-remote.md').write_bytes(concurrent)
            git('add', '--', 'new-remote.md', cwd=other)
            git('commit', '-m', 'concurrent update', cwd=other)
            git('push', 'origin', 'HEAD:refs/heads/main', cwd=other)
            expected = git('rev-parse', 'HEAD', cwd=other).stdout.strip()
            result = git('push', 'origin', 'HEAD:refs/heads/main', cwd=checkout, ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(git('--git-dir', str(remote), 'rev-parse', 'main').stdout.strip(), expected)
            self.assertEqual(git('--git-dir', str(remote), 'show', 'main:remote-only.md', text=False).stdout, preserved)
            self.assertEqual(git('--git-dir', str(remote), 'show', 'main:new-remote.md', text=False).stdout, concurrent)
            self.assertEqual((checkout / 'approved.md').read_bytes(), approved)


if __name__ == '__main__':
    unittest.main()
