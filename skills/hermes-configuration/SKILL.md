---
name: hermes-configuration
description: Practical Hermes Agent configuration patterns — memory providers, auxiliary models, provider reuse, and retrieval debugging. Companion to the bundled hermes-agent skill.
version: 1.0.0
author: agent
tags: [hermes, configuration, memory, auxiliary, CJK, opencode]
---

# Hermes Configuration Patterns

Practical configuration workflows and pitfalls for Hermes Agent. This skill covers memory provider setup, auxiliary model routing, provider reuse, and CJK retrieval verification — the patterns that go beyond what `hermes config set` alone teaches you. Companion to the bundled `hermes-agent` skill (which covers CLI reference, tools, and architecture).

**Load this skill when:**
- Configuring external memory providers (Holographic, Hindsight, etc.)
- Setting up auxiliary models (vision, compression, title generation, etc.)
- Reusing an existing provider for auxiliary tasks
- Debugging CJK (Chinese/Japanese/Korean) search in session_search
- Configuring or changing Hermes memory/model architecture

---

## 1. Memory Provider Setup

### Holographic (local, zero API cost)

**Pitfall:** Holographic requires numpy. If numpy is missing, it silently degrades — no error, just broken retrieval. Always install first.

```bash
# 1. Install numpy in Hermes venv (known pitfall — skip this, silent failure)
~/.hermes/hermes-agent/venv/bin/python3 -m pip install numpy

# 2. Enable Holographic
hermes config set memory.provider holographic

# 3. Verify
hermes memory status
# Expected: Provider: holographic, Plugin: installed ✓, Status: available ✓

# 4. Restart session (required — memory provider initializes at session start)
# In CLI: /reset
# In gateway: /restart
```

### Other providers

```bash
hermes memory setup    # Interactive selector (requires PTY)
hermes memory off      # Disable external provider, back to built-in only
```

---

## 2. Auxiliary Model Configuration

Hermes uses separate models for auxiliary tasks (vision, compression, title generation, etc.). If `auxiliary.*.provider` is `auto` and no API key is configured, these tasks fail silently.

### Pattern: Reuse main provider for all auxiliary tasks

All auxiliary tasks can share the same provider. Only vision needs special attention (must be a multimodal model).

```bash
# Batch-set all auxiliary providers (adjust model per task)
hermes config set auxiliary.vision.provider opencode-go
hermes config set auxiliary.vision.model glm-5          # multimodal required

hermes config set auxiliary.compression.provider opencode-go
hermes config set auxiliary.compression.model deepseek-v4-pro

hermes config set auxiliary.web_extract.provider opencode-go
hermes config set auxiliary.web_extract.model deepseek-v4-pro

hermes config set auxiliary.skills_hub.provider opencode-go
hermes config set auxiliary.skills_hub.model deepseek-v4-pro

hermes config set auxiliary.approval.provider opencode-go
hermes config set auxiliary.approval.model deepseek-v4-pro

hermes config set auxiliary.mcp.provider opencode-go
hermes config set auxiliary.mcp.model deepseek-v4-pro

hermes config set auxiliary.title_generation.provider opencode-go
hermes config set auxiliary.title_generation.model deepseek-v4-flash  # lightweight

hermes config set auxiliary.triage_specifier.provider opencode-go
hermes config set auxiliary.triage_specifier.model deepseek-v4-pro

hermes config set auxiliary.kanban_decomposer.provider opencode-go
hermes config set auxiliary.kanban_decomposer.model deepseek-v4-pro

hermes config set auxiliary.profile_describer.provider opencode-go
hermes config set auxiliary.profile_describer.model deepseek-v4-pro

hermes config set auxiliary.curator.provider opencode-go
hermes config set auxiliary.curator.model deepseek-v4-pro
```

**Model selection rules:**
- **Vision** → must be multimodal (e.g., `glm-5`, `mimo-v2-omni`)
- **Title generation, triage** → lightweight model saves cost (e.g., `deepseek-v4-flash`)
- **Everything else** → use the main model for consistency

**Verification:**
```bash
grep -A2 "provider: opencode-go" ~/.hermes/config.yaml
```

---

## 3. OpenCode Go Model Discovery

To list available models on opencode-go (or any OpenAI-compatible provider):

```bash
curl -s "https://opencode.ai/zen/go/v1/models" \
  -H "Authorization: Bearer $(grep OPENCODE_GO_API_KEY ~/.hermes/.env | grep -v '^#' | cut -d= -f2)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]"
```

Current model catalog (May 2026):
- `deepseek-v4-pro`, `deepseek-v4-flash`
- `glm-5`, `glm-5.1`
- `kimi-k2.5`, `kimi-k2.6`
- `minimax-m2.5`, `minimax-m2.7`
- `mimo-v2-pro`, `mimo-v2-omni`, `mimo-v2.5-pro`, `mimo-v2.5`
- `qwen3.6-plus`, `qwen3.5-plus`
- `hy3-preview`

---

## 4. CJK Retrieval Verification

Hermes has a 3-path CJK routing system (`hermes_state.py` lines 2212-2315):

| Path | Trigger | Mechanism | Pros | Cons |
|------|---------|-----------|------|------|
| unicode61 FTS5 | No CJK chars in query | Default FTS5 | Indexed, ranked, fast | CJK chars split into single tokens |
| trigram FTS5 | ≥3 CJK chars AND every token ≥3 chars | `messages_fts_trigram` table | Indexed, ranked, phrase-aware | Fails for 1-2 char tokens |
| LIKE fallback | <3 total CJK or any short token | Full-table LIKE scan | Works for any CJK query | No ranking, linear scan |

### Verification queries

```bash
# Check if trigram table exists and is populated
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages_fts_trigram;"

# Test CJK routing paths
sqlite3 ~/.hermes/state.db "
SELECT 'trigram path (≥3 chars):' as test;
SELECT rowid, snippet(messages_fts_trigram, 0, '[', ']', '...', 30)
FROM messages_fts_trigram WHERE content MATCH '环境变量' LIMIT 3;
"
```

### Key insight
Short CJK queries (1-2 characters like "飞书") use LIKE with OR semantics across tokens. Multi-token queries like "飞书 配置" match any message containing EITHER term, not both. For AND semantics, use a single quoted phrase.

**Code reference:** `hermes_state.py::search_messages()`, CJK detection at `_contains_cjk()` and `_count_cjk()`, token-length check at #20494.

---

## 5. Restart Considerations

Most configuration changes require a fresh session to take effect:
- Memory provider changes → `/reset` (CLI) or `/restart` (gateway)
- Auxiliary model changes → `/reset`
- Toolset changes → `/reset`

Only `config.yaml` writes take effect immediately; anything that initializes at session start needs a restart.

---

## References

- `references/cjk-routing-detail.md` — Full code-level detail of the 3-path CJK routing in `hermes_state.py::search_messages()`, including pseudocode, detection ranges, path selection examples, and LIKE fallback OR semantics.
- `references/opencode-go-provider.md` — OpenCode Go provider configuration: model discovery, current catalog, recommended model-to-task mapping, and the `auto` provider silent-failure pitfall.
- `references/hermes-update-workflow.md` — Step-by-step update procedure: HTTP2 workaround, local change stash/restore, gateway restart requirements, and rollback path.

---

## 6. Update Workflow

### Full procedure

```bash
# 1. Check for updates
hermes update
# If this fails with HTTP2 error, use the git workaround below

# 2. Git workaround (when HTTP2 is flaky)
cd ~/.hermes/hermes-agent
git -c http.version=HTTP/1.1 fetch origin

# 3. Check what's changed
git log --oneline HEAD..origin/main

# 4. Pull — local modifications WILL block this
git -c http.version=HTTP/1.1 pull --ff-only origin main
```

### Handling local modifications

If you've patched Hermes source files (plugin fixes, tool changes, etc.), `git pull` will abort with "Your local changes would be overwritten". The safe workflow:

```bash
# Stash only the files you changed (not everything)
git stash push -m "descriptive name" -- tools/foo.py plugins/bar/__init__.py

# Pull
git -c http.version=HTTP/1.1 pull --ff-only origin main

# Re-apply your changes (auto-merge handles most cases)
git stash pop
# If conflicts: resolve manually, then 'git stash drop'
```

**Pitfall:** If upstream modified the same files you changed, `stash pop` may conflict. The `git stash` stack holds your changes safely — you can always `git stash list` and recover.

### After update

```bash
# Restart gateway for code changes to take effect
hermes gateway restart
# Note: this kills the current session; conversation history is preserved
```

**What needs restart vs what doesn't:**

| Change type | Needs |
|-------------|-------|
| Plugin code (any `.py` in `plugins/`) | Gateway restart |
| Tool code (`tools/*.py`) | Gateway restart |
| `config.yaml` edits | `/reset` (new session) |
| `.env` edits | Gateway restart |
| Skill files (`SKILL.md`) | `/reset` |
| New skills added to `~/.hermes/skills/` | `/reset` or `/reload-skills` |

### Rollback

If the update breaks something:

```bash
cd ~/.hermes/hermes-agent
git reflog                          # find the pre-update commit
git reset --hard <commit-hash>      # revert
hermes gateway restart              # apply reverted code
```

### Skill install from personal tap repo

When `hermes skills install` from URL requires interactive prompts that can't be satisfied in gateway mode (category picker, confirmation), and the repo is trusted:

```bash
# Clone and copy directly
cd /tmp && git clone --depth 1 <personal-skills-repo-url>
cp -r /tmp/<repo>/skills/<skill-name> ~/.hermes/skills/<skill-name>
# Skill is available after /reload-skills or /reset
```

See the full update procedure in `references/hermes-update-workflow.md`.
