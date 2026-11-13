# Isolated test suite

Run from the repository root with Python 3.8 or newer:

```sh
python -m unittest discover -s tests -v
```

All filesystem and Git behavior fixtures use temporary directories. These tests do not certify a real Obsidian vault, agent runtime integration, or external companion skill behavior.

## Prerequisites and skips

- Shell entrypoint and dependency checks need `bash` on PATH. They are explicitly **skipped**, not passed, when Bash is absent.
- The disposable Git test needs Git on PATH and is skipped when it is absent.
- POSIX permission-bit assertions are skipped on Windows. Windows ACL preservation is not covered.
- Installer symlink tests skip only when Windows reports missing symlink-creation privilege (WinError 1314); other setup errors still fail. No privilege escalation is attempted.
- Canvas symlink coverage reports a skip when symlink creation is unavailable.

Always report both passing and skipped tests. A successful run with skips is not evidence that the skipped features work. Bash being present also does not prove that its path conventions interoperate with native Windows Python.

## Native Python smoke coverage

`test_python_install_smoke.py` runs without Bash. It installs all three real packages into isolated directories, repeats installation, checks installed bytes and ownership markers, then runs the installed Canvas repair/verification CLI on a synthetic file. It invokes the internal Python installer directly, so it does **not** exercise shell dependency checks or certify the public shell entrypoints.

For just these smoke tests:

```sh
python -m unittest discover -s tests -p test_python_install_smoke.py -v
```

## Optional workflow acceptance preparation

[Synthetic acceptance preparation](../docs/optional-workflow-experiments.md)
provides deterministic DOCX/canary fixtures and bounded output checks for future
MarkItDown/Gitleaks experiments. The unit tests exercise only the generator and
checker; they do not run, install, or certify either external tool. A matching
synthetic output is not proof of tool execution, network isolation, or real-data
readiness.

## QMD source snapshot races

`test_qmd_source_snapshot.py` exercises the public literal-search reader using
synthetic file and parent-directory replacements, symlink substitutions, and
changes during reading. A POSIX-only FIFO substitution check verifies that a
replacement special file does not block opening; it is skipped on Windows.
The reader compares path and descriptor identities before returning content and
rejects symlinks/reparse points. These are bounded snapshot checks, not a lock or
an isolation guarantee against a malicious concurrent filesystem writer.

## Installer path-entry checks

`test_install_reparse.py` verifies conservative rejection of Windows reparse
attributes before directory descent. A native Windows junction fixture checks
refusal through a parent path and confirms the synthetic destination stays empty.
That native check skips on non-Windows; mocked attribute checks run everywhere.
The installer refuses all reparse points, including legitimate cloud placeholders,
rather than guessing their semantics. Use ordinary local directories. This does
not exclude concurrent non-cooperating filesystem writers; stop runtimes and sync
and use a trusted workspace. No real vault or machine settings are touched.
