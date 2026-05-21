# Workflow Modes

## `orient`

Use `orient` when:

- entering a vault for the first time in a session
- resuming after a long context gap
- the request is ambiguous
- the request references a vault but does not yet justify writing

Work in this order:

1. Read anchor files such as `SCHEMA.md`, `index.md`, `log.md`, `AGENTS.md`, and vault guide notes.
2. Probe the vault structure only if the anchors are missing or incomplete.
3. Infer the active note roles, stable frontmatter fields, and navigation system.
4. Decide whether the next step belongs to `answer`, `ingest`, or `audit`.

Default rule:

- `orient` is read-only

## `answer`

Use `answer` when the user wants understanding rather than file changes.

Answer flow:

1. Decide whether the vault alone is enough.
2. Read the smallest relevant set of source, knowledge, project, and system notes.
3. Distinguish between source-backed facts, vault-level synthesis, and claims that still need fresh verification.
4. If the question is current, contested, high-impact, or asks for external verification, use a fresh-check path when an external search companion such as `anysearch` is available.
5. Answer clearly and conservatively.

Default rule:

- do not create or update notes unless the user explicitly asks
- do not send private vault content to external search providers unless the user explicitly approves

### `fresh-check` path inside `answer`

Use `fresh-check` when the vault may be stale or insufficient.

Preferred behavior:

1. Start from the vault so the answer remains grounded in the user's existing context.
2. Form the narrowest external queries needed to verify the claim.
3. Use `anysearch` only when external freshness, vertical search, or batch discovery adds value.
4. Label external results as fresh evidence candidates.
5. Do not write the result back unless the user asks for filing or the workflow moves into `ingest`.

## `ingest`

Use `ingest` when the user wants new material folded into the vault.

Ingest flow:

1. Identify the current source-note convention.
2. Preserve the new material in the source layer first.
3. Decide whether the source justifies changes to knowledge or project notes.
4. Update indexes, dashboards, or log notes only when that matches the vault's existing habits or clearly improves navigation.
5. Summarize exactly what changed.

Default rule:

- do not spread a single source across many notes unless the value is clear
- do not append low-value noise to `log.md`

### Source discovery inside `ingest`

Use optional external search before or during ingest when:

- the supplied source is weak, partial, or disputed
- the user asks for corroboration
- the target knowledge note needs stronger evidence coverage
- a project note needs current external facts

If `anysearch` is available, use it for external discovery and vertical searches. Save or cite only sources that pass the normal source-note and evidence rules.

## `audit`

Use `audit` when the user wants to check vault health or repair maintenance drift.

Audit scope:

- structure
- navigation
- metadata
- relationships
- evidence traceability
- duplication
- stale or weak synthesis

Default rule:

- read first, then propose or apply targeted fixes

### `lint` sub-mode

Treat `lint` as the default sub-mode inside `audit`.

Use it when the user asks to:

- lint the vault
- run a health check
- find navigation drift
- inspect weak evidence
- check schema, index, or log consistency

Lint checklist:

- structure health
- navigation health
- metadata coverage
- relationship quality
- evidence traceability
- stale or weak synthesis
- schema, index, or log drift when those files exist
- active log bloat and rotation hygiene when the vault uses `log.md`
- evidence gaps that may benefit from external source discovery

Default rule:

- report findings first
- do not repair automatically unless the user asks for fixes or the task already includes repair

### Evidence-gap search inside `lint`

When lint finds weak or unverified knowledge claims, optionally use `anysearch` to discover candidate sources.

Rules:

- do not auto-promote discovered results into knowledge notes
- report candidate sources separately from verified fixes
- only update source or knowledge notes after the user asks for repair or ingest
- avoid sending sensitive vault content as search queries

### Log rotation inside `audit`

When a vault uses `log.md`, treat it as a recent operational journal rather than a permanent monolith.

Preferred behavior:

1. Keep `log.md` short enough to scan quickly.
2. Rotate older entries into archival files such as `log-2026.md` or another vault-native naming pattern.
3. Preserve a summary or index note if archived logs are important to navigation.
4. During lint, flag logs that have become too long, too noisy, or no longer useful as recent-history views.
