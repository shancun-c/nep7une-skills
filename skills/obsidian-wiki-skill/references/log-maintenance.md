# Log Maintenance

## Purpose

Use `log.md` to track meaningful vault maintenance history, not to capture every interaction.

Good candidates for logging:

- source ingest
- audit or lint runs
- repair passes
- bulk renames or retagging
- schema or index changes
- major restructures

Usually skip:

- ordinary read-only answers
- exploratory chat with no file impact
- tiny edits that add no future value to the maintenance trail

## Active Log Versus Archive

Treat `log.md` as the active log.

It should answer:

- what changed recently
- which maintenance actions happened
- where to look next

Once it becomes too long to scan comfortably, rotate older entries into archive files.

Common patterns:

- `log-2026.md`
- `log-2026-q2.md`
- `logs/2026/2026-05.md`

Use the naming pattern that best matches the host vault.

## Rotation Triggers

Rotate when one or more of these are true:

- the log reaches a few hundred entries
- recent activity is buried under stale history
- the file becomes slow or annoying to scan
- the vault owner already uses time-sliced archival notes elsewhere

Do not hard-code a single numeric threshold for every vault. Prefer readability and host conventions over rigid rules.

## Rotation Workflow

1. Create the archive target using a vault-native naming pattern.
2. Move older entries out of `log.md`.
3. Leave `log.md` as a short recent-history view.
4. If needed, create or update a summary note that points to archived logs.
5. Mention the rotation in the active log or maintenance summary if that helps future orientation.

## Lint Expectations

Inside `audit -> lint`, flag:

- logs that are too large to scan comfortably
- logs that contain too much low-value noise
- missing archive links when the vault clearly depends on historical maintenance records
- mismatches between active logs and index/schema conventions
