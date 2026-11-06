# Installation maintenance and recovery

These instructions apply to the repository's Bash/Python installers, not to
third-party tap managers. Keep a separate backup of personal data. Installation
backups are not a substitute for a vault backup.

## Before any update

1. Stop the host runtime, editor, and sync client. No noncooperating process may
   write the target during the update.
2. Record the current source commit and intended skills root/target. Review the
   new source before executing it. Do not blindly replace it with a moving ref.
3. Run the same installer with the same explicit skill and target plus
   `--dry-run`. Inspect the reported target. Dry run writes no target files/locks.
4. Remove `--dry-run` only after the preview succeeds and the target is correct.
5. Confirm installed files, local configuration/state, and runtime discovery.
   Validate in a test vault before using personal data.

## What the installer preserves or refuses

- A fresh target may be absent or an empty dedicated directory.
- A nonempty target must have a valid `.nep7une-install.json` ownership manifest.
  Do not create or edit a manifest to bypass ownership protection.
- Locally modified managed files cause refusal rather than silent overwrite.
  Permission-only edits are preserved. Unrelated files and legacy
  `references/canvas-state.md` are retained.
- Obsolete package files are retained, not pruned. Use a new dedicated directory
  if an upgrade requires removal of obsolete files.
- Symlink paths/trees are refused. Use an explicitly selected real directory;
  do not change system permissions to get around a refusal.
- Content-changing updates stage a complete copy and preserve the old installation in a
  `SKILL-UUID` directory within `.nep7une-skill-backups` beside the skills root,
  outside skill discovery. Backups may include private configuration/state.
  Keep them private; never upload them to a public repository.
- Custom targets on another filesystem may be refused when directory rename
  cannot cross filesystems. Keep staging/backup/target on a compatible filesystem.

## Migrating a legacy install

Older installs without this installer's manifest are not automatically adopted.
Install into a **new** dedicated skills root, verify it, and compare your old
configuration and state with the new copy. Migrate only reviewed local data,
then update the runtime's discovery configuration using its documented process.
Keep the old installation until the new one is validated; avoid discovering both
versions simultaneously. This guide does not perform the migration for you.

## Interrupted update or rollback

There is no automated rollback command in this version. If installation is
interrupted between directory renames, preserve the target, staging directory,
backup, and reported diagnostics. Confirm no installer or other writer is still
running before investigating a stale lock. Do not simply delete a lock to retry.

Inspect the recorded backup and compare its manifest/content with the intended
previous version. Restore a reviewed previous directory only after isolating the
current one and stopping all writers. Validate local state and discovery again.
A directory swap is not a fully atomic multi-file transaction, and final snapshot
checks cannot prevent a writer from modifying files immediately afterwards.

## Uninstalling

There is no uninstall command. First stop the runtime and remove or disable its
discovery of this collection using the runtime's own supported procedure.
Inspect the exact installed skill directory and save any local state or private
configuration before manually removing that directory. Do not remove the whole
skills root: it may contain unrelated skills. Preserve required companions used
by other workflows. Backup removal is a separate, deliberate action after
validation, not an automatic part of uninstalling.

## Troubleshooting

| Symptom | Meaning / safe next step |
| --- | --- |
| Required dependency missing | Install the trusted required companion in the selected skills root; check the dependency table. Do not use bypass as proof of readiness. |
| Missing ownership manifest | Legacy or unrelated nonempty target; use a new dedicated root and review migration. |
| Managed file changed | Preserve local edits and compare with source before deciding how to migrate. |
| Invalid target name / symlink | Check skill name and use a real dedicated target directory. |
| Lock or backup/stage remains | Confirm no active writer, preserve evidence, and inspect recovery state before any retry. |
| Install succeeds but runtime cannot see skill | Files copied successfully does not imply runtime discovery; check the runtime's documented search paths and nested collection support. |
| Canvas check fails | Read the exact structural/color errors; it is not a full schema/layout check. Preview any repair on a copy first. |
