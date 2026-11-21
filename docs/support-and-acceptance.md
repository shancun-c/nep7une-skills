# Platform evidence and release acceptance

This checklist separates verification evidence from support guarantees.
Record the exact source commit and candidate diff with
every run. Results from another revision remain historical evidence, even when
only documentation changed. A local run is not hosted CI.

## Separate the claims

| Layer | What a passing check establishes | What it does not establish |
| --- | --- | --- |
| Offline Python suite | The collected synthetic checks passed on the recorded Python/OS | Skipped cases, another OS, a real vault, or companion behavior |
| Bash syntax | The shell files parse with the recorded Bash | Execution, dependency availability, or Windows path interoperability |
| Empty-target preview | The explicit package/target plan passed validation without installing | Successful copying, upgrade/rollback, dependency readiness, or runtime discovery |
| Native Python install smoke | Three packages install/reinstall in temporary directories; synthetic Canvas CLI works | Public Bash entrypoints or external companion behavior |
| Runtime discovery | A separately observed host runtime finds the intended installed skill | Permission to operate a real vault/server or correctness of external tools |

A platform row should be `not run`, `passed with skips`, `passed`, or `failed`,
with a date, revision, runtime versions, command, and test/skip counts. Never turn
an absent runner, an empty Actions list, or a mock into native-platform evidence.

## Historical Linux candidate evidence

See the dated evidence below for this documentation-only candidate. There is no
claim of native Windows, native macOS, hosted CI, companion execution, or real
runtime discovery. The native Windows junction test is skipped on Linux; mocked
reparse-attribute tests are not a substitute. Windows also has separate ACL,
symlink-privilege, Bash/Python path, and file-identity considerations.

Run on 2026-11-19 UTC against base
`15cd4eecb9664fb0bce50561508c261be35d5a8d` with a separately applied documentation-only candidate diff adding this guide
and its README link. The held registry-identity draft (#14) is excluded; the
QMD-budget change (#17) is part of the base.

| Environment/check | Observed result |
| --- | --- |
| Debian 13 x86_64, CPython 3.12.14 | 211 collected: 210 passed, 1 native Windows junction test skipped |
| Bash 5.2.37, installer shell syntax | All four `installers/*.sh` files passed syntax checks |
| Three shell entrypoints × three skills | Nine `--skip-deps --dry-run` previews passed; temporary parent remained empty after each |
| Git 2.52.0 | Available for the suite's disposable local Git tests |
| Native Windows / macOS | Not run for this candidate |
| Hosted CI / runtime discovery / external companions | Not verified by this local run |

These counts are a dated observation, not an expected permanent suite size.
Re-run and update the evidence before claiming acceptance of another revision.

## Reproduce in a disposable checkout

Review the source first. Run from its root with Python 3.8+; Bash and Git are
needed for their integration cases. Record the output and all skips, not just the
exit status. Missing tools can produce skips rather than failures.

```sh
git rev-parse HEAD
git status --short
python3 --version
bash --version
git --version
python3 -m unittest discover -s tests -v
for script in installers/*.sh; do bash -n "$script" || exit; done
```

Run just the public installer preview matrix with:

```sh
python3 -m unittest discover -s tests -p test_installer_previews.py -v
```

The full offline suite already includes this matrix. It checks each of the
three skills through all three Bash entrypoints, using both documented target
modes (18 isolated cases). Each preview checks the exact reported destination
and leaves its own temporary parent empty. For Codex and Hermes, the
`--target` case uses an explicit full skill directory; for OpenClaw, it uses a
workspace. `--skip-deps` is deliberate: this is not a dependency check or an
installation. Both tests skip without Bash and on native Windows, where Bash
path interoperability is not assessed. The native Python smoke suite is
separate; do not record skipped previews as passed.

If a command fails, stop and retain its diagnostics. Do not bypass a dependency,
ownership, symlink/reparse, local-edit, or state-file/directory refusal to make
this checklist green. Review unexpected output before cleaning it up.

## Native Windows acceptance slices

Use a clean disposable checkout and an ordinary local temporary directory,
not a synced folder, real vault, or runtime skills root. Run the following from
the checkout root in PowerShell. Use native Windows CPython; WSL does not
exercise Windows junction behavior. The tests do not need Bash and should not
require administrator privileges or changes to system settings. If the Python
launcher is not installed, use the full path of an existing native
`python.exe` in place of `py -3`.

```powershell
git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$dirty = git status --short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($dirty) { throw 'Use a clean disposable checkout.' }
py -3 -c "import os, platform; assert os.name == 'nt'; print(platform.platform(), platform.python_implementation(), platform.python_version(), platform.machine())"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
py -3 -m unittest discover -s tests -p test_install_reparse.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
py -3 -m unittest discover -s tests -p test_python_install_smoke.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

Record the interpreter, commit, and exact test outcomes. In particular, verify
that `test_native_junction_parent_and_tree_refused_before_install` ran and
passed, rather than being skipped. A failure to create the disposable junction
is an unfulfilled test prerequisite, not evidence of installer refusal. Do not
change permissions or privileges to get a green result.

The reparse slice combines mocked attributes with actual junction refusal
before traversal or installation. The smoke slice runs the internal Python
installer against disposable targets, verifies install/reinstall, and exercises
the installed Canvas scripts on synthetic data. These results do not cover the
public Bash entrypoints on Windows, ACL preservation, real runtime skill
discovery, companion tools, or an actual vault.

**Recorded Windows evidence (2026-11-20 UTC):** On Windows 10 build 19045,
CPython 3.12.14 (AMD64), the targeted slices passed 4/4 and 2/2 without skips,
respectively, against content verified from commit
`eccb8ac5fbfe8ba781ea7c26350d2bbe934a703b` (tree
`860aa9aecb04eba8c6b90c8f52889bd445f57ec8`). The run verified 33 scoped
source and fixture blobs. It did not run a full Windows suite, the Windows
Bash matrix, a macOS test, or hosted CI. Treat this as dated evidence, not a
claim about another revision.

## Release review gates

- [ ] Pin the base commit and reviewed candidate diff; exclude unrelated drafts.
- [ ] Record exact OS/Python/Bash/Git versions and full results, including skips.
- [ ] Check both public preview matrix tests above and the native Python smoke
  suite.
- [ ] Check required-companion refusal tests; separately verify any real
      companion/runtime integration being claimed, with explicit authorization.
- [ ] Validate the actual archive bytes if distributing an archive. Checkout
      tests alone do not validate packaging, executable modes, or archive layout.
- [ ] Review the [maintenance and recovery guide](maintenance.md). Preserve
      valid local state; do not describe recoverable updates as atomic rollback.
- [ ] Leave untested platforms/features explicitly unverified. Obtain native
      runners before upgrading their support claim.
- [ ] Inspect actual hosted checks and repository review/merge requirements;
      local acceptance does not waive them or authorize a merge/release.

No command here configures a scheduler, SSH, a real vault, or an external search
index. See [test scope and skips](../tests/README.md) and
[isolated examples](examples.md) for their separate limits.
