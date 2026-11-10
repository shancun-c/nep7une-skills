# Synthetic acceptance preparation for optional workflows

This is a fixture generator and a narrow output checker, **not a MarkItDown or
Gitleaks runner**. It installs nothing, starts no subprocess, performs no network
requests, and reads no real document or vault. It is separate from the frozen
first-phase workflow patch and adds no required runtime dependency.

## What is executable now

`tools/optional_workflow_acceptance.py` uses only Python's standard library. It
can create a new synthetic fixture directory under an existing private workspace:

```sh
python tools/optional_workflow_acceptance.py --write-fixtures /path/to/private-workspace/synthetic-fixtures
```

The directory must not already exist. Existing destinations and symlink parents
are refused. The workspace must be trusted and free of concurrent writers;
these checks are not a filesystem race defense. POSIX modes are requested for
new directories but do not establish Windows ACL privacy. Partial fixture output
may remain after an I/O failure; inspect it before an authorized cleanup.

The generator writes only original synthetic material:

- `source.docx`: deterministic OOXML containing English and Chinese text,
  citation/data markers, and a three-column, two-data-row financial table.
- `clean/clean.txt`: an innocuous negative-control input.
- `canary/canary.txt`: a clearly synthetic token on line 2, not a credential.
- `gitleaks.toml`: one narrowly defined custom rule for that synthetic token.
- `manifest.json`: byte counts and SHA-256 hashes of the generated inputs.

The two scanner cases are separate directories. Do not scan the entire bundle,
which also contains configuration, source material, and the opposite test case.
The manifest is an identity record, not signed attestation or execution proof.

## Output checks

The module exposes two pure functions that receive bytes already collected by
an authorized test runner. They do not read paths or execute tools:

- `check_markdown(payload)`: verifies preservation of four fixed source markers
  and a specific Markdown table, including year/value/unit relationships. Missing
  Unicode, swapped values, flattened units, or duplicate/conflicting tables return
  `not_verified`. Alternate valid representations such as HTML tables need manual
  review; this is not a general Markdown parser or full document-fidelity test.
- `check_gitleaks(payload, returncode=..., case=..., expected_file=...)`: verifies
  the clean JSON report or one synthetic canary finding with a distinct findings
  exit code of 10. The caller must derive `expected_file` from the authorized
  invocation, never copy it from an untrusted report to make a check pass.

The Gitleaks check requires the expected rule, exact source file label, line 2,
and fully replaced synthetic `Secret`/`Match` values. It rejects known canary
content anywhere in decoded JSON, non-null fragments, duplicate JSON keys,
non-finite numbers, malformed/oversize inputs, scope mismatches, and error exits.
Its summary never includes report text, paths, metadata, or secret values.
Unknown metadata is discarded, not certified as redacted. Do not publish the
input report merely because the reduced summary passes.

Both functions return only fixed-vocabulary summaries. Even a passing result
explicitly records:

- scope: `synthetic_output_only`;
- tool execution: `not_verified`;
- network isolation: `not_verified`;
- real-data readiness: `not_verified`.

A fabricated matching output can pass this narrow checker. It is not evidence
that a converter/scanner ran, that a pinned version was used, or that the process
had no network access. The future invocation harness must establish those facts
separately and bind input/configuration/tool hashes to the run.

## Before an actual tool experiment

Use the existing [local document workflow](../skills/obsidian-wiki-skill/references/local-document-ingest.md)
and [publication scan workflow](../skills/obsidian-wiki-skill/references/publication-secret-scan.md).
Choose reviewed installed tools and an authorized isolated environment. Do not
install dependencies, change security settings, or upload data as a fallback.

For MarkItDown, convert only `source.docx`, keep plugins/cloud clients disabled,
and capture Markdown privately with a real return code and bounded execution.
Compare the output to the original document as well as using the checker. This
small DOCX does not establish PDF, scanned-page/OCR, XLSX, or PPTX support.

For Gitleaks, use explicit configuration, separate clean/canary directories,
full redaction, and a configured findings exit code of 10. Capture reports and
diagnostics privately. The custom canary rule tests basic invocation/output
contracts, **not the default rules' detection coverage or false-negative rate**.
Before adopting a version, verify its actual file-label and exit behavior. A
different result requires investigation, not weakening a test to manufacture a
pass. Standard output, standard error, temporary reports, and any report fields
outside this check still need independent redaction review.

No actual MarkItDown/Gitleaks integration run is claimed by this change. They
were not installed in the preparation environment. Actual-version, network,
resource-boundary, Linux/Windows, and malformed-document experiments remain
pending. Production integration and real-vault access remain out of scope.

## Regressions

```sh
python -m unittest discover -s tests -p test_optional_workflow_acceptance.py -v
python -m unittest discover -s tests -v
```

All new unit tests use original in-memory output or temporary synthetic files.
They verify the checker and generator, not external converters/scanners. The
symlink regression explicitly skips only Windows privilege error 1314; report
that skip separately from passes. Do not suppress other setup errors.

## Source-grounded privacy distinction

The reviewed Gitleaks implementation replaces secret text in `Secret`, `Match`,
and `Line`; that does not mean all report metadata is anonymized. Its finding
structure contains other metadata and optional fragments. That is why this
checker emits a new minimal summary instead of forwarding a redacted report.
This is a boundary observation, not a claim of a verified upstream vulnerability.

References: [finding fields and redaction](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/report/finding.go),
[JSON reporter](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/report/json.go),
[empty-report fixture](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/testdata/expected/report/empty.json).
The generator and checker are original code; no upstream implementation is copied.
