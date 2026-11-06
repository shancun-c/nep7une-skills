# Git Sync Safety for Obsidian Vaults

## Default: local only

Local editing does not authorize publication. Ingest and audit-repair finish with
local changes and a report by default. A configured remote is not authorization.
Publish only when the user explicitly authorized the destination repository,
branch, and file scope. A standing permission must cover this exact publication.
Missing permission or configuration pauses publication only, not permitted local work.
Never use a personal repository or author-specific path as a fallback.

## Non-negotiable boundaries

- Never initialize Git in the live vault or perform Git writes there.
- Never reset vault files, force-push, rewrite remote history, or delete remote-only
  files to make a sync succeed. The remote is not assumed stale or disposable.
- Never copy the entire vault or stage all files indiscriminately. Use an explicit
  reviewed file allowlist; exclude credentials, private configuration, runtime state,
  caches, and unrelated files. Recheck sensitive material even on an allowed path.
- Never copy `.git` metadata. Reject symlinks, absolute paths and `..` components in
  the allowlist; resolve both source and destination within their respective roots.
- Do not treat a timeout, rejected push, or divergence as permission to use a more
  destructive command. Stop and report the actual state.

## Separate-checkout publication procedure

This is a manual safety policy, not an automatic sync implementation. No command
below grants permission. Complete the checks in order for every publication.

1. Resolve [vault-config.md](vault-config.md). Verify exact remote URL, branch,
   checkout path and allowed files against the user's authorization. The checkout
   must be independent of and outside the vault; neither directory may contain
   the other. If the checkout is missing, create a fresh clone of the approved
   repository outside the vault. Stop if cloning or authentication fails.
2. Require a clean checkout and no unrelated staged changes. Verify its current
   branch, repository root, fetch URL and **all push URLs**, not just its folder
   name. Stop on a mismatch; do not silently alter remote configuration. Disable
   automatic publication by companion tools for this local-edit workflow.
3. Fetch the approved branch. Require the checkout HEAD to equal that branch's
   fetched remote tip before copying. If ahead, behind, or diverged, stop and
   review the difference separately. Do not reset, merge, rebase, or force a sync
   as an automatic recovery step.
4. Record the fetched tip. Preview the approved files individually. Copy only
   those regular files into the independent checkout, preserving all remote-only
   and unrelated files. Do not use deletion mirroring. A deletion or overwrite
   of independently changed remote content needs separate review and permission.
5. Review the full diff and stage only the approved relative paths. Inspect the
   staged diff again for sensitive data, unexpected deletion, binary content,
   and any path outside the allowlist. Abort if the staged set differs from the
   approved set. If there is no change, report that and stop without committing.
6. Commit the reviewed changes locally on top of the recorded remote tip. Fetch
   again immediately before publication and require that the remote tip still
   matches the recorded tip. If it changed, stop without pushing; leave the
   local commit available for review.
7. Use an ordinary fast-forward push to the exact approved branch, with an
   explicit refspec and no force options. A concurrent remote update can still
   occur after the check: the ordinary push must reject it, not overwrite it.
   On rejection or uncertainty, stop and inspect the remote before retrying.
8. Read back the remote tip and files. Report publication only after the expected
   commit and file set are verified. A successful local commit is not a publish.

## Recovery and failures

If a destructive command was previously run, stop further writes. Look for a
verified backup, editor history, filesystem snapshots, or repository history.
Do not promise that a cloud-sync provider has recoverable versions. Present the
available recovery choices without overwriting the user's current files.

For network or authentication failures, report the exact blocked step and keep
local work intact. Do not change credentials, system settings, repository access,
or legal agreements as an automatic fallback.
