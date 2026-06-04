# Git Sync Pitfalls for Obsidian Vaults

> Common failures when syncing a local Obsidian vault with a remote Git repository, and the safe patterns to use instead.

## Core Rule

**Never use `git reset --hard` on a vault working tree.** The local vault holds the latest content; the remote is usually stale. `reset --hard` replaces local files with old remote versions, destroying uncommitted work.

## Common Failure Chain

1. Clone fails/timeouts because the repo is large (binary media, many commits)
   → Symptom: `fetch-pack: unexpected disconnect while reading sideband packet`
2. Agent tries `git init` + `git remote add` + `git fetch` in the vault directory
3. Fetch succeeds (possibly needing `http.postBuffer` tweak)
4. Agent tries `git checkout -b main origin/main` → fails because local files would be overwritten
5. Agent escalates to `git reset --hard origin/main` → **destroys local changes**

## Safe Pattern: Init-in-Place with Merge

When you need to sync a local vault that has no `.git` directory to a remote:

```bash
# 1. Init git in the vault
cd /path/to/vault
git init
git remote add origin <remote-url>

# 2. Fetch remote (use http.postBuffer for large repos)
git -c http.postBuffer=524288000 -c core.compression=0 fetch --depth 1 origin main

# 3. Inspect the diff FIRST — never reset
git diff origin/main --stat | head -50

# 4. If the diff looks reasonable, create a commit on top
git add -A
git commit -m "sync: local vault updates $(date +%Y-%m-%d)"

# 5. Force-push (only if you're sure local is the authoritative version)
git push origin main -f
```

## Alternative: Clone + Rsync

When the remote repo is too large for in-place init:

```bash
# Clone into a temp directory
git clone --depth 1 <remote-url> /tmp/vault-temp

# Rsync local changes onto the clone (preserving .git)
rsync -a --exclude='.git' --exclude='.obsidian/workspace.json' \
  /path/to/vault/ /tmp/vault-temp/

# Commit and push from the temp clone
cd /tmp/vault-temp
git add -A
git commit -m "sync: local vault updates $(date +%Y-%m-%d)"
git push origin main
```

## SSH Clone Timeout

Large repos with many binary files (screenshots, PDFs, videos) can time out over SSH. Try these in order:

```bash
# 1. Increase buffer size (first attempt)
git clone --depth 1 -c http.postBuffer=524288000 <remote-url>

# 2. Blobless clone — fetches commit/tree objects only, skips large binaries.
#    Clone succeeds but checkout may still time out if blobs are needed.
git clone --depth 1 --filter=blob:none <remote-url>

# 3. Blobless clone + sparse checkout — only checkout markdown files.
#    Eliminates binary download/checkout entirely. Then rsync vault content on top.
git clone --depth 1 --filter=blob:none <remote-url> /tmp/vault-temp
cd /tmp/vault-temp
git sparse-checkout init --cone
git sparse-checkout set '*.md' '*.yaml' '*.json' 'AGENTS.md' 'SCHEMA.md'
git checkout main
rsync -a --exclude='.git' --exclude='.obsidian' /path/to/vault/ ./
```

## Push Timeout

Large repos may also time out on `git push`. Increase the buffer and timeout:

```bash
git -c http.postBuffer=524288000 push origin main
```

## Pre-push Safety Checklist

Before any `git push --force` on a vault repo:

- [ ] Confirm this is the user's personal vault (not a shared repo)
- [ ] Confirm the local vault has the latest content (not a stale clone)
- [ ] Confirm no other collaborators have pushed to the remote since the last sync
- [ ] If unsure, ask the user before force-pushing

## Recovery After Reset --hard

If `git reset --hard origin/main` was already executed:

1. **Google Drive users**: Files have version history. Right-click → "Manage versions" (Google Drive web) or Finder → "Revert To" (macOS client). Restore the overwritten files one by one.
2. **Non-Drive users**: Check local backup (Time Machine, etc.) or the remote's git history for the most recent content.
3. **Last resort**: Reconstruct changes from session history (what the agent did in the current conversation).
