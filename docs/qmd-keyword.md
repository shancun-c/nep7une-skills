# QMD keyword prototype: production and live-index query disabled

Base main: `18ace7163b67d1d942df574d53c1b5c41b76ca0e`. All merged kepano
files are preserved. This patch is synthetic-only experimental scaffolding,
not an installer, deployed integration, or authorization to read a real vault.

## Current status: sealed synthetic queries verified

The third-stage sealed-copy query path has been implemented and exercised with
actual QMD and concurrent writes to the original index. The general public API
and the older live-index query path remain disabled. These are different paths;
this document does not claim that all querying is disabled.

## Current supported boundaries

- Public `tools/qmd_keyword.py:search()` always uses explicit-scope literal
  fallback. Passing enabled=True does not execute QMD. It reports the blocked
  state. `_search_experiment` is internal regression scaffolding, not a safe
  activation API.
- Public literal fallback reads and matches each authorized file separately rather
  than retaining the entire corpus. It continues checking files after the hit
  limit to preserve unavailable-source diagnostics. The per-file byte limit is
  unchanged; filenames, diagnostics and selected snippets still use memory.
  Total file count and total scan time are not capped, and this is not an atomic
  snapshot of files that other processes can edit concurrently. Internal QMD
  experiments retain their existing source-snapshot behavior.
- `search_active_synthetic` also rejects calls: no reliable exclusion of other
  SQLite writers during QMD's live-index query has been established. Users may
  explicitly use literal fallback separately; invalid generations never silently
  become accepted QMD queries.
- `search_sealed_synthetic` performs the verified synthetic sealed-copy query
  described below. It is experimental and does not enable a real-vault workflow.
- Builder/inspection tests only accept an explicit synthetic confirmation,
  caller-supplied root and Markdown file allowlist. They do not enumerate any
  real vault or automatically broaden scope, install software, generate models,
  run update hooks, or start servers. New generations use fresh private config.
- All subprocesses use bounded stdout, discarded stderr, disconnected stdin,
  timeout and strict UTF-8 decoding. NODE_OPTIONS/NODE_PATH are removed centrally,
  including QMD build/version commands, Unicode normalizer and query experiments.
  This is not a sandbox against a hostile executable or descendant process tree.

## Current generation build and acceptance

`qmd_index_experiment.py` stages exactly the authorized synthetic files in a new
private generation, runs pinned official QMD 2.8.3 collection add, and verifies
collection scope, stored content and source snapshots. It binds original/staged
root, collection, QMD version/executable, config, source hashes and index identity
and random generation. Manifest writes are fsynced then atomically renamed.

`qmd_generation.py` additionally binds Node and every file/safe link in the supplied
runtime tree. It verifies FTS filepath/title/body normalization against the
pinned QMD Unicode Script contract, and FTS integrity on an in-memory copy.
Expected document bodies are grounded independently in manifest hashes AND
re-read original/staged sources, never solely in the index's content table.
Unexpected active documents and stored content are rejected.

SQLite inspection always copies bounded main DB bytes (maximum 64 MiB), verifies
the copy against the manifest digest, then opens this private copy using
mode=ro&immutable=1. No unbound WAL can be merged into the inspected view. Any
-wal, -shm or -journal entry (including zero-byte entries and symlinks) causes
rejection before and after copying/inspection. Main file identity is rechecked.
The 64 MiB ceiling applies before and during every index identity hash, not only
when copying into SQLite. Identity checks reject observed non-regular files
before opening them, compare the opened descriptor with the pre-open metadata,
and detect size/identity changes after reading. This is not an atomic open or a
hostile-filesystem sandbox: a malicious writer can still replace a path between
checks, including with a special file before open. Use trusted private synthetic
workspaces without concurrent writers. No process-tree or network isolation is
established by these file checks.
These checks detect observed changes; they do NOT lock other writers or prove a
live QMD query used the verified view. That is why live query remains disabled.

An atomic synthetic-only active pointer can select an accepted experimental
generation for inspection. Verification rechecks expected generation, pointer,
attestation/manifest identity, root/collection, sources, config/index, runtime and
FTS. Evidence statuses remain explicitly experimental; nothing activates public
search. Atomic visibility is not serialized multiwriter arbitration. Parent-dir
crash durability and production writer locking remain unimplemented.

## Regression evidence and historical correction

The earlier second-stage experiment executed a real synthetic QMD query and
reported successful FTS verification. Independent review then demonstrated
WAL_TAMPER_ACCEPTED: main DB identity stayed unchanged while WAL coherently changed
content.doc and FTS.body. That earlier evidence is NOT sufficient acceptance and
must not be used to claim a safe enabled integration.

The revised regression creates that same condition with an open WAL writer,
asserts main DB identity remains identical, and verifies rejection. Additional
checks reject coherent content/FTS tampering even if index metadata is refreshed,
reject empty journals, and show immutable inspection sees original content during
a concurrent WAL write then rejects the live sidecar at exit. Environment tests
verify injected NODE_OPTIONS/NODE_PATH do not reach Node. At that WAL-hardening
stage, the actual-QMD rebuild verified snapshot/FTS/active-generation inspection
only and did not execute queries. This is historical evidence: the subsequent
third stage implemented and verified sealed-copy queries, as documented below.

Run `python3 -m unittest discover -s tests`. Node-required exact-Unicode tests
explicitly skip if Node is absent. Symlink tests explicitly skip if platform
permissions prohibit creation. No Windows/macOS runtime pass is claimed.

## Remaining work before any production activation

- Preserve the independently reviewed sealed-copy isolation model when designing
  a production interface. Sealed synthetic querying is already implemented;
  production deployment, privacy controls and performance remain unvalidated.
  Do not re-enable the older live-index query path based on pre/post stat checks.
- Define trusted manifest ownership/selection and mutation policy. These local
  records are not signed attestation against an attacker able to rewrite both
  artifacts and metadata.
- Recheck concurrent pointer/file replacement boundaries and add crash tests.
- Measure larger synthetic corpora: full runtime hashing, source re-reading and
  FTS verification per query are not a production-scale performance design.
- Obtain separate explicit real-vault scope and platform-specific privacy/ACL
  validation before any real data integration. Keep config/index/cache outside
  vault/Git and owner-only; the prototype does not silently change permissions.

No code was committed, published or merged by this experiment.

## Current third-stage sealed query experiment

`search_sealed_synthetic` is a separate internal synthetic experiment. Public
`search` and old `search_active_synthetic` remain disabled for QMD execution.
After active-generation acceptance, the new path copies the checked immutable DB
view into a fresh owner-private temporary directory. QMD receives only this new
INDEX_PATH and copied trusted configuration, never the live-generation DB. It
can create its own journals there; after process exit those must be gone before
content/FTS verification. The temporary copy is removed on success or failure.

A successful response identifies the captured generation and snapshot digest.
Writes to the original generation after capture do not change that query's
snapshot semantics. Original source files are re-read/checked at return; source
changes cause rejection rather than returning a stale or substituted excerpt.
Pointer/attestation/manifest changes cause rejection. A later query must accept
the original generation afresh, so a mutated original index cannot silently
become the next accepted snapshot. Updating source data requires explicitly
building, accepting and selecting a new generation; old-generation queries are
rejected. No automatic update hook or indexing is performed by search.

This protects query isolation from writers of the ORIGINAL index. It is not an
OS sandbox or write-exclusion guarantee against another same-user process able
to discover and mutate the private query copy while QMD runs. Post-query content
validation catches observed copy changes but does not prove absence of transient
hostile changes. No production safety or performance readiness is claimed.

The opt-in integration harness is `tests/run_qmd_sealed_experiment.py`. Pass an
explicit local pinned npm runtime directory; it creates only temporary synthetic
files, runs actual QMD, writes the original index concurrently through WAL,
checks that original-source hits remain identical, verifies rejection after
source mutation, and verifies new results after an explicit new-generation
rebuild. It does not run automatically with unittest or download/install QMD.

Historical regression run before the Windows fixes: 94 unittest tests passed on Linux. The actual-QMD
sealed-concurrency experiment separately passed original-WAL isolation, original
source-change rejection, explicit new-generation update, and temporary-copy
cleanup. These results do not constitute a Windows/macOS or production pass.

## Historical Windows follow-up (failures resolved)

A later Windows run of the earlier 94-test patch reported 5 failures, 32 errors
and 14 skips. The Linux 94-pass result above remains historical Linux evidence,
not cross-platform acceptance. Two identified causes are addressed here:

- Python's SQLite connection context manager ends a transaction but does not
  close the connection. Snapshot, sealed-copy destination and fixture connections
  now use explicit closing; transaction fixture contexts still commit/rollback.
  A regression retains connection references and checks they are closed after
  both successful snapshot inspection and an injected exception.
- Synthetic newline fixtures are written as explicit UTF-8 bytes, and indexed
  hashes use the same byte-preserving `_read` path as verification. Dedicated
  CRLF tests prove the hash matches the actual UTF-8 bytes and that an LF-normalized
  hash cannot falsely authenticate a CRLF source. Line display may use splitlines;
  evidence hashing never normalizes source newlines.

The final Windows rerun below supersedes this stage. These fixes do not enable any public QMD path,
read real vaults, or change the experimental deployment boundary.

## Historical Windows interrupted rerun and bounded test diagnostics

A subsequent Windows rerun stopped without a final summary after 41 passes and
12 skips; last completed was `test_installed_canvas_cli_on_synthetic_file`.
Under standard unittest discovery its next test is
`test_real_packages_install_and_reinstall_without_bash`, which invokes nine
Python installer subprocesses (three skills, each dry-run/install/reinstall).
Those subprocess calls previously had no timeout. This identifies the next
scheduled work, NOT the verified Windows hang cause. The installer does not
invoke Git, so an independent dubious-ownership warning does not establish the
cause. Process diagnostics were denied; no permissions or safe.directory setting
was changed, and that denial must not be bypassed.

The test subprocess helper now uses a 30-second default deadline, direct-child
cleanup with a five-second wait, disconnected stdin, and file-backed output so
inherited stdout PIPE handles cannot cause an unbounded communicate-after-kill
wait. Output is bounded, and start/exit diagnostics identify the command phase.
This applies to existing canvas/dependency/Git/install/native-smoke subprocess
tests as well as new timeout, UTF-8 and no-input regressions. A timeout is an
error, not a skipped or successful test. Cleanup permission errors report the
unverified child and stop; no process enumeration, tree kill or escalation is
attempted. The QMD subprocess helper's final wait is also bounded to five seconds.
The later final-summary run below completed; this interrupted run itself was not a pass.
The harness does not promise descendant-tree cleanup. A descendant retaining an
output-file handle can make Windows temporary-file cleanup fail; that error is
reported, not bypassed or converted to success. This specific native Windows
handle-inheritance scenario has not been verified here. Running/exited-child
output-limit regressions are included in addition to timeout and diagnostics.
The 30-second child deadline starts after Popen returns; it cannot bound an OS
process-creation call itself. The 4 MiB output threshold is polled and checked
before accepting results, not an OS-enforced disk-write quota; temporary output
may overshoot between polls. These are test diagnostics limits, not a hostile
process resource sandbox.

## Historical Git preservation fixture newline follow-up (failure resolved)

The next Windows run completed all 102 tests (87 passed, one failure, 14 skipped).
The sole failure was a fixture CRLF/LF comparison in test_git_policy.py; the earlier
SQLite connection errors did not recur. The fixture now writes and compares exact
bytes, including `git show` captured with text=False. It does not strip or normalize
newlines, so corruption still fails. Disposable Git invocations specify
`-c core.autocrlf=false` only for that command; no Git configuration or safe.directory
setting is written. The final Windows rerun below passed this exact code revision.


## Final cross-platform regression status

The final Windows run completed all 102 tests: 88 passed, 14 skipped, and zero
failures or errors. The tested patch SHA-256 was
`e03065459aac4969c0506e1ed9a3fa68703dba60a4c8659860b9c01e548bec5c`.
This result was reported by the coordinating Windows execution; the local Linux
run completed all 102 tests with no skips or failures. The earlier SQLite-handle
and Git-fixture newline failures are resolved in this revision. The 14 Windows
skips are not passes and do not demonstrate coverage of the skipped cases.

This final documentation update changes no code or tests; its regenerated patch
necessarily has a different digest from the Windows-tested patch above. The
Windows interrupted-run cause remains unproven, even though the later complete
run ended normally. Platform-specific limits and unverified scenarios described
above remain applicable. These regression results do not constitute production
or macOS acceptance. Public QMD search remains disabled; experiments use only
synthetic data, with no real vault access or automatic model download.

## Bounded normalization batches (synthetic experiment follow-up)

The former single-payload 200KB inspection limit is superseded only within this
synthetic experiment by whole-row batches, each still capped at 200,000 bytes.
Fixed cumulative budgets are 2,000,000 input bytes, 8,000,000 output bytes,
2,048 rows, 32 processes and 10 seconds shared by normalization invocations.
Single-row oversize and cumulative preflight violations fail before starting
Node. Each child retains a 1MB output cap. The deadline excludes initial source
and DB scanning and subsequent integrity checking; this is not an OS resource
quota. Exact FTS comparison and existing immutable DB capture remain required.
All original and staged source hashes are rechecked after the batches. This
catches persistent changes, not malicious transient changes between sequential
checks; no source lock or same-user hostile-process protection is claimed.

A synthetic SQLite/Node envelope with 512 tiny Chinese/English documents now
passes (232,850-byte combined payload), while last-document FTS substitution
still fails. The fixture was not built by actual QMD and proves neither real
QMD recall nor production large-vault performance. The opt-in harness is
`tests/run_qmd_inspection_scale.py`; no install or model download is performed.
The initial QMD regression subset passed 54 tests on Linux/Python 3.12.14.
Follow-up coverage adds malformed-output rejection and decreasing cross-batch
time/output allowances; mock-only budget tests also run without Node. The full
updated Linux suite passed 117 tests with no skips on Python 3.12.14.
Independent review found no blocking regression. No new Windows, Python 3.8,
or actual pinned-QMD integration run is claimed.
Public search remains disabled and real vault access is outside this experiment.

### Literal source snapshots

The literal reader checks each source's regular-file identity against its opened
file descriptor, before and after a bounded read, and checks the canonical root
and parent-directory identities. Detected replacements, symlinks/reparse points,
or changes during reading are reported in `unavailable`, without returning that
source's content. The supplied root is resolved before use, as before; its resolved
target defines the authorized scope. This is a per-file check, not an atomic
corpus snapshot or a guarantee of isolation from malicious concurrent writers.
