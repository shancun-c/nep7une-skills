"""Pre-spawn budget checks use mocks, never unbounded child processes."""
import io
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import qmd_keyword as qmd


class RunnerBudgets(unittest.TestCase):
    def test_invalid_timeout_refused_before_spawn(self):
        for value in (None, '1', True, 0, -1, float('nan'), float('inf'), -float('inf'),
                      qmd.threading.TIMEOUT_MAX * 2, 10 ** 400):
            with self.subTest(value=value), patch.object(
                    qmd.subprocess, 'Popen', side_effect=AssertionError('spawn attempted')) as spawn:
                with self.assertRaisesRegex(ValueError, 'timeout'):
                    qmd._bounded_run(['unused'], timeout=value)
                spawn.assert_not_called()

    def test_invalid_output_budget_refused_before_spawn(self):
        for value in (None, '1', True, -1, 1.5, float('nan'), float('inf')):
            with self.subTest(value=value), patch.object(
                    qmd.subprocess, 'Popen', side_effect=AssertionError('spawn attempted')) as spawn:
                with self.assertRaisesRegex(ValueError, 'output byte budget'):
                    qmd._bounded_run(['unused'], max_bytes=value)
                spawn.assert_not_called()

    def test_valid_finite_budgets_keep_exact_output_limit(self):
        for timeout, budget, payload in ((1, 0, b''), (0.5, 2, b'ok')):
            process = SimpleNamespace(stdout=io.BytesIO(payload),
                                      wait=Mock(return_value=0), poll=Mock(return_value=0))
            with self.subTest(timeout=timeout, budget=budget), patch.object(
                    qmd.subprocess, 'Popen', return_value=process) as spawn:
                result = qmd._bounded_run(['unused'], timeout=timeout, max_bytes=budget)
                self.assertEqual(result.stdout, payload.decode())
                spawn.assert_called_once()


if __name__ == '__main__':
    unittest.main()
