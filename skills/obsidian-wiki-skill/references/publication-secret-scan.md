# Optional publication secret scan

Use Gitleaks as an additional local check before an already authorized
publication. This reference does not implement scanning, install software,
authorize reading secrets, or grant permission to publish. A configured remote,
clean scanner report, or presence of this reference is not permission.

## Scope and preparation

Follow steps 1–5 of git-sync-pitfalls.md for scope, checkout preparation, and
staged review, then pause before step 6 (commit) and step 7 (push). Do not finish
that publication procedure first. Select exactly the approved files in an
independent checkout or disposable staging export outside the real vault.
Never scan the whole vault, home directory, server, or unrelated repository as a
convenient default. Never copy `.git` from the vault. Reject symlinks and path
escapes before preparing the export; do not let the scanner expand the scope.

If secrets may be present, verify that the user's authorization covers local
inspection of this exact material. Keep the tool and results local. Do not
send documents, credentials, or findings to a third-party scanning service.
No scanner binary is bundled here. Verify the existing binary's provenance and
version, or follow the host's approval process for official installation.

Review which configuration and ignore rules will apply. Gitleaks can load
GITLEAKS_CONFIG, GITLEAKS_CONFIG_TOML, and repository configuration. An unexpected
allowlist, ignore file, or disabled rule can hide findings. Do not silently trust
or rewrite those inputs, broaden exceptions, or mark a scan successful when the
effective configuration is unknown. Record the binary and configuration hashes.
An explicit `--config` does not bypass ignore files: the reviewed implementation
also loads `.gitleaksignore` from the source directory and the selected ignore
path (the working directory by default). Inspect both locations, and do not pass
a baseline or extra ignore file unless it is explicitly part of the reviewed
scope. Do not delete or rewrite existing ignore files to force a clean result.

## Choose the correct coverage

1. For a staged file export, use the `dir` mode on that exact disposable directory.
   This checks selected current contents, not Git history or a Git index.
2. For approved commit-history review, use `git` mode with an explicitly reviewed
   commit range in the independent checkout. This scans Git patches and is not a
   substitute for checking uncommitted current file contents.

Do not assume one mode covers the other. Do not scan all history unless that
scope is authorized. For the narrow initial experiment, explicitly pass
`--max-archive-depth=0 --max-decode-depth=0`. In the reviewed version, archive
traversal defaults to 0 but recursive decoding defaults to 5; omitting these
options does not establish the intended disabled behavior. This narrower mode
can miss encoded secrets and archives; record that coverage limit rather than
claiming a comprehensive scan. Expansion requires a separately reviewed need.

Pass exactly one validated, nonempty source path to `dir`, as one argument, and
use a private disposable working directory. The reviewed implementation falls
back to the working directory if it receives zero or multiple positional
arguments. Do not build the invocation by splitting or interpolating a shell
command string, or pass several files as separate positional arguments. Put `--`
before the source path so a path cannot be interpreted as an option.

Require full redaction (`--redact=100`), avoid verbose output, and keep stdout,
stderr, and any report private. Redaction of secret values does not necessarily
remove sensitive paths, source lines, usernames, or commit metadata. Do not
publish raw JSON/SARIF reports, CI artifacts, or terminal logs. Verify report
redaction on synthetic canaries before relying on it. Produce a new sanitized
summary containing only approved file identifiers, rule IDs, and counts.
For JSON reports, prefer `--report-format=json --report-path=-` with stdout
captured privately and separately from stderr by the bounded runner. If using a
file report, use a fresh dedicated path outside the scan scope: the reviewed
implementation creates and removes the report path during preflight, so an
existing file there can be truncated and removed even before scanning begins.
Use a trusted directory without concurrent writers; a fresh-path check alone is
not protection against a path replacement race.

Use bounded execution. A missing binary, timeout, truncated output, parse error,
or unknown exit status means **not verified**, never a pass. The documented
default exit code 1 combines findings and errors. If using a distinct configured
findings code (for example `--exit-code=10`), verify that behavior against the
installed version and still inspect sanitized diagnostics. Do not mistake a
scanner runtime failure for a clean or merely finding-bearing scan.

## Findings and publication gate

- Report potential secrets without displaying their values. A finding may be a
  false positive; a clean scan may miss a secret or unrelated private information.
- Stop publication on an unresolved finding. Do not automatically add allowlists,
  delete files, rewrite history, rotate credentials, or contact another party.
- Keep the manual staged diff and privacy review required by git-sync-pitfalls.md.
  Secret scanning does not detect every address, private note, identity document,
  or other information unsuitable for publication.
- Bind the result to the reviewed file hashes or commit range. Any subsequent
  content, staging, configuration, or tool change invalidates that result and
  requires a fresh check. Preserve all existing remote/branch/allowlist checks.
- Report scan mode, selected scope, tool/configuration versions, outcome, and
  verification limits. Publication remains a separate authorized operation.

## Acceptance still required before executable integration

Use only synthetic canaries. Test clean files, a synthetic matching token,
current-content versus historical coverage, config/ignore tampering, path escapes,
redacted diagnostics, timeouts, and finding/error exit handling. Confirm no
secret-like fixture or report enters logs/artifacts. Test each platform separately.
No Gitleaks integration run or false-negative guarantee is claimed here.

## Sources

- [Gitleaks CLI, configuration, reporting, and exit behavior](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/README.md)
- [Reviewed CLI defaults, ignore loading, report preflight, and exit handling](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/cmd/root.go)
- [Reviewed directory argument handling](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/cmd/directory.go)
- [Gitleaks MIT license](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/LICENSE)

This reference is original workflow guidance. It uses the standalone CLI model;
it does not install a GitHub Action, request new credentials, or change hooks.
