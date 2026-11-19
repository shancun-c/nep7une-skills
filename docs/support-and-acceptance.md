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

## Current local candidate evidence

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

Exercise all nine explicit runtime/skill plans without touching a runtime's real
skills root. `--skip-deps` is deliberate here: this verifies packaging only, not
required companion installation. No install is performed by these commands.

```bash
preview_root="$(mktemp -d)" || exit
for runtime in codex hermes openclaw; do
  for skill in knowledge-canvas-sync obsidian-wiki-skill server-ops-skill; do
    bash "installers/install-$runtime.sh" \
      --skills-dir "$preview_root/$runtime" --skill "$skill" \
      --skip-deps --dry-run || exit
  done
done
# Successful previews must leave the temporary parent empty.
rmdir "$preview_root"
```

If a command fails, stop and retain its diagnostics. Do not bypass a dependency,
ownership, symlink/reparse, local-edit, or state-file/directory refusal to make
this checklist green. Review unexpected output before cleaning it up.

## Release review gates

- [ ] Pin the base commit and reviewed candidate diff; exclude unrelated drafts.
- [ ] Record exact OS/Python/Bash/Git versions and full results, including skips.
- [ ] Check all nine previews above and the native Python smoke suite.
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
