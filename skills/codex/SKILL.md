---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g --include=optional @openai/codex` (the `--include=optional` flag ensures the platform-specific binary is downloaded — critical on macOS)
- OpenAI auth configured: either `OPENAI_API_KEY` or Codex OAuth credentials
  from the Codex CLI login flow
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

For Hermes itself, `model.provider: openai-codex` uses Hermes-managed Codex
OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. For the
standalone Codex CLI, a valid CLI OAuth session may live under
`~/.codex/auth.json`; do not treat a missing `OPENAI_API_KEY` alone as proof
that Codex auth is missing.

### Installation Pitfalls

**ENOTEMPTY error on reinstall.** If a previous install was corrupted or partial,
npm will fail with `ENOTEMPTY: directory not empty, rename …/@openai/codex`.
Manually move the stale directory out of the way before retrying:
```bash
mv $(npm config get prefix)/lib/node_modules/@openai $(npm config get prefix)/lib/node_modules/@openai_stale
# then retry
npm install -g @openai/codex
```
Deleting via `rm -rf` can hang on macOS with large node_modules trees — `mv`
is faster and equally effective.

**Slow install on macOS (npmjs.org bandwidth from China).** The `@openai/codex`
tgz is large (~130MB compressed, ~211MB uncompressed). From China, npmjs.org
can deliver as little as 16KB/s, making the install take hours or produce
truncated binaries. **Use a Chinese npm mirror** instead:

```bash
npm install -g --registry=https://registry.npmmirror.com @openai/codex@latest
```

This alone often resolves slow downloads and truncation issues. If the global
node_modules has stale `@openai` directories from prior failed installs, use
the clean-directory approach below instead of global install.

**Do NOT use `--no-optional`** — it skips the darwin binary and the CLI will
fail with `Missing optional dependency @openai/codex-darwin-x64`. If you need
to force inclusion of optional deps:
```bash
npm install -g --include=optional @openai/codex
```

**Clean-directory install (avoids global node_modules lockup).** When the
global `node_modules/@openai` directory is corrupted from prior failed installs
and even `mv` or `rm -rf` time out (common with very large npm caches on macOS),
install to a fresh temporary directory instead:

```bash
mkdir -p /tmp/codex-install && cd /tmp/codex-install
npm init -y
npm install --registry=https://registry.npmmirror.com @openai/codex@latest
# Binary is at: node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex
# Link it:
ln -sf /tmp/codex-install/node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex \
       "$(npm config get prefix)/bin/codex"
codex --version  # verify
```

This completely sidesteps the global node_modules lockup and ENOTEMPTY
conflicts, and when combined with the mirror, completes in under 30 seconds.

**Darwin binary is a dist-tag, not a separate package.** The optional
dependency `@openai/codex-darwin-x64` is declared as an npm alias:
`"npm:@openai/codex@0.132.0-darwin-x64"`. It's not a standalone package on the
registry — it's the same `@openai/codex` main package published under a
version tag. When optional deps fail to resolve (silent npm failure), install
the darwin build directly via dist-tag:
```bash
npm install -g @openai/codex@0.132.0-darwin-x64
```
Then symlink the binary if needed:
```bash
ln -sf "$(npm root -g)/@openai/codex/node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex" \
       "$(npm config get prefix)/bin/codex"
```

**"Missing optional dependency @openai/codex-darwin-x64".** This error means
the darwin platform binary was not installed. Causes:
- `--no-optional` was used during install → use `--include=optional` instead
- npm silently skipped the optional dep (cache corruption, registry flakiness)
Fix: install the darwin dist-tag directly (see above), or reinstall with
`--include=optional`.

**macOS: binary killed by Gatekeeper (Killed: 9).** If `codex --version`
silently exits with `Killed: 9`, the Codex binary is unsigned and macOS
Gatekeeper is blocking it. The binary may also be corrupted from an incomplete
npm extraction — check its size (`du -sh`) and run `codesign -dv` to confirm
it reads "code object is not signed at all". If `codesign --force --sign -`
fails with "main executable failed strict validation", the binary is damaged
and must be reinstalled from scratch.

**Truncated binary from corrupt npm cache.** The most insidious failure mode:
npm has a cached copy of the darwin tarball that was partially downloaded.
On reinstall, npm reuses the corrupt cache entry, producing a binary that's
a fraction of its real size (e.g. 12 MB instead of ~211 MB). The Mach-O
headers claim `filesize` values exceeding the actual file size (`otool -l`
shows "past end of file"), and macOS kills the process with SIGKILL because
the binary fails strict validation. The fix is to bypass npm's cache
entirely — download the tarball directly with curl:

```bash
# Get the download URL for your platform
TGZ_URL=$(npm view @openai/codex@0.132.0-darwin-x64 dist.tarball)
curl -L -o /tmp/codex.tgz "$TGZ_URL"

# Extract and install manually (avoids npm cache)
tar -xzf /tmp/codex.tgz -C /tmp/codex-pkg
cp /tmp/codex-pkg/package/vendor/x86_64-apple-darwin/codex/codex \
   "$(npm config get prefix)/bin/codex"
chmod +x "$(npm config get prefix)/bin/codex"
codex --version  # should now work
```

**npm cache too large for cleanup.** On systems where Codex has been
installed and reinstalled multiple times, the npm cache can grow so large
that `rm -rf`, `find`, and `npm cache clean --force` all timeout (>30s).
When you hit this, skip cache operations entirely. Either use the direct
curl download above, or truncate the cache surgically:

```bash
# Instead of `npm cache clean --force`, remove only codex entries
rm -rf "$(npm config get cache)/_cacache/content-v2/sha512/"$(echo -n "@openai/codex" | shasum -a 256 | cut -d' ' -f1)
```

then retry the install. This targets only the corrupt cache entries without
touch the rest of the (large) cache.

**macOS: npx may also fail.** When `npm install -g` is unreliable, `npx` can
sometimes work — it downloads to a separate cache and runs in one step:
```bash
npx --yes @openai/codex --version
```
However, `npx` suffers from the same optional-dependency problem: if the
darwin binary isn't fetched, it produces the same `Missing optional dependency`
error. If `npx` fails, fall back to the direct dist-tag install above.

**Non-standard npm prefix.** If `which codex` returns nothing after install,
check the npm prefix and ensure its `bin/` directory is on PATH:
```bash
npm config get prefix   # e.g. ~/.hermes/node
ls "$(npm config get prefix)/bin/codex"
export PATH="$(npm config get prefix)/bin:$PATH"
```

For detailed error traces and diagnostic commands for macOS-specific install
failures, see `references/macos-install-errors.md`.

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox workspace-write` | Allows file writes within workspace (default is `read-only`) |
| `--ask-for-approval never` | Skip all approval prompts |
| `-C / --cd DIR` | Set working root directory |

### Non-interactive exec sandbox pitfall (read-only by default)

`codex exec` in non-interactive mode defaults to `sandbox: read-only`. It will read files and plan changes but **cannot write any files**. This manifests as silent hangs or zero-output timeouts — Codex processes the task but fails on the first write attempt.

**Fix**: Always pair `codex exec` with sandbox and approval flags for file-creating tasks:
```bash
codex exec "build a project" --sandbox workspace-write --ask-for-approval never
```

**Background terminal PTY issues**: When running `codex exec` in `terminal(background=true)`, the process may fail with `tcsetattr: Inappropriate ioctl for device` because there's no real terminal. For file-heavy build tasks, prefer Hermes-native tools (write_file, patch, terminal) over delegating to Codex in background mode — it's faster and avoids sandbox/PTY complexity.

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch, or add the directory to `~/.codex/config.toml` trusted projects (see below)
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work

## Workspace Configuration

Codex supports a persistent workspace directory via `~/.codex/config.toml`. When configured, Codex can operate in directories listed as trusted projects without needing a git repo:

```toml
[projects."/Users/nep7une/codex-workspace"]
trust_level = "trusted"
```

Then use `-C` to set the working root at launch:
```bash
codex exec "build a project" -C /Users/nep7une/codex-workspace/my-project
```

For new projects, combine with AGENTS.md rules to enforce project-creation conventions:

```markdown
## Workspace Rule

All new projects MUST be created under `/Users/nep7une/codex-workspace/<project-name>/`.
Never create project files directly in the home directory or other locations.
```

### "Not inside a trusted directory" error

If Codex refuses with "Not inside a trusted directory and --skip-git-repo-check was not specified":

1. **Preferred fix**: `git init && git add -A && git commit -m "init"` — makes the directory a git repo
2. **Alternative**: Add the directory (or its parent) to `~/.codex/config.toml` under `[projects]` with `trust_level = "trusted"`
3. **Quick bypass**: Pass `--skip-git-repo-check` flag (only for directories you trust)

The `--cd` / `-C` flag tells Codex which directory to use as its working root, but does NOT bypass the git/trust check — the directory still needs to be a git repo or explicitly trusted.
