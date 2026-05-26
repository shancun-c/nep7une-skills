# server-ops-skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `server-ops-skill` to the `nep7une-skills` collection as a public, credential-safe SSH server operations skill.

**Architecture:** Implement a workflow-first skill under `skills/server-ops-skill/` with concise core instructions and focused reference files. Keep real server facts in ignored local `.private/` profiles, and integrate the new skill into the collection README, registry, validators, and installers without committing secrets.

**Tech Stack:** AgentSkills Markdown format, YAML registry metadata, shell-based installers, Codex skill validator.

---

## File Map

- Create: `skills/server-ops-skill/SKILL.md`
- Create: `skills/server-ops-skill/agents/openai.yaml`
- Create: `skills/server-ops-skill/references/ssh-safety.md`
- Create: `skills/server-ops-skill/references/server-orientation.md`
- Create: `skills/server-ops-skill/references/service-operations.md`
- Create: `skills/server-ops-skill/references/deployment-workflow.md`
- Create: `skills/server-ops-skill/references/private-profile-template.md`
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `registry.yaml`
- Local only: `.private/server-profiles/nep7une-tokyo.md`

## Task 1: Create Skill Files

- [ ] **Step 1: Create `skills/server-ops-skill/` directories**

Run:

```bash
mkdir -p skills/server-ops-skill/agents skills/server-ops-skill/references
```

Expected: directories exist.

- [ ] **Step 2: Add `SKILL.md`**

Write a public `SKILL.md` with:

- frontmatter `name: server-ops-skill`
- a broad trigger description for SSH-based Linux server operations
- modes: `orient`, `inspect`, `deploy`, `repair`, `rollback`, `harden`
- default SSH alias policy
- private profile policy
- safety and confirmation rules
- routing to reference files

- [ ] **Step 3: Add reference files**

Create focused reference files:

- `ssh-safety.md`: credential, SSH, confirmation, and redaction rules
- `server-orientation.md`: read-only inventory workflow
- `service-operations.md`: systemd, Nginx, Docker, PM2, logs, TLS checks
- `deployment-workflow.md`: deployment, validation, and rollback workflow
- `private-profile-template.md`: sanitized local profile template

- [ ] **Step 4: Add `agents/openai.yaml`**

Create UI metadata:

```yaml
interface:
  display_name: "Server Ops Skill"
  short_description: "Safe SSH server operations"
  default_prompt: "Use $server-ops-skill to inspect and manage my SSH-accessible server safely."
```

## Task 2: Integrate Collection Metadata

- [ ] **Step 1: Update `.gitignore`**

Add:

```gitignore
.private/
```

- [ ] **Step 2: Update `registry.yaml`**

Add `server-ops-skill` with:

- path `skills/server-ops-skill`
- runtime install paths under `nep7une-skills/server-ops-skill`
- empty skill dependencies for Codex, Hermes, and OpenClaw because the dependency is a local `ssh` tool, not another skill

- [ ] **Step 3: Update `README.md`**

Add `server-ops-skill` to the available skills table, repository layout, dependency notes, validation notes, and example prompts.

## Task 3: Add Local Private Profile

- [ ] **Step 1: Create ignored profile directory**

Run:

```bash
mkdir -p .private/server-profiles
```

Expected: `.private/` is ignored by Git.

- [ ] **Step 2: Write sanitized local profile**

Create `.private/server-profiles/nep7une-tokyo.md` with only non-secret operational facts and no raw credentials.

- [ ] **Step 3: Confirm profile is not tracked**

Run:

```bash
git check-ignore -v .private/server-profiles/nep7une-tokyo.md
```

Expected: `.gitignore` ignores the file.

## Task 4: Validate and Install

- [ ] **Step 1: Validate skill**

Run:

```bash
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/server-ops-skill
```

Expected: `Skill is valid!`

- [ ] **Step 2: Run installer dry-runs**

Run:

```bash
installers/install-codex.sh --skill server-ops-skill --dry-run
installers/install-hermes.sh --skill server-ops-skill --dry-run
installers/install-openclaw.sh --target /tmp/openclaw-server-ops-test --skill server-ops-skill --dry-run
```

Expected: all point to `nep7une-skills/server-ops-skill` and do not fail dependency checks.

- [ ] **Step 3: Install into Codex and Hermes**

Run:

```bash
installers/install-codex.sh --skill server-ops-skill
installers/install-hermes.sh --skill server-ops-skill
```

Expected: files sync to:

```text
~/.codex/skills/nep7une-skills/server-ops-skill
~/.hermes/skills/nep7une-skills/server-ops-skill
```

- [ ] **Step 4: Validate installed copies**

Run:

```bash
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/wenweikun/.codex/skills/nep7une-skills/server-ops-skill
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/wenweikun/.hermes/skills/nep7une-skills/server-ops-skill
```

Expected: both return `Skill is valid!`

## Task 5: Secret Scan and Commit

- [ ] **Step 1: Scan tracked changes for secrets**

Run:

```bash
git diff --cached --name-only
git diff -- ':(exclude).private/**'
rg -n '198\\.13|PRIVATE KEY|BEGIN OPENSSH|password|passwd|TOKEN=|SECRET=|API_KEY=|\\.env=' . --glob '!.git/**' --glob '!.private/**'
```

Expected: no raw server credentials in tracked files. Generic safety words such as `password` may appear only as prohibitions.

- [ ] **Step 2: Commit**

Run:

```bash
git add .gitignore README.md registry.yaml skills/server-ops-skill docs/superpowers/plans/2026-05-26-server-ops-skill.md
git commit --author="nep7une <nep7une@users.noreply.github.com>" -m "feat: add server ops skill"
```

Expected: commit succeeds.

- [ ] **Step 3: Push**

Run:

```bash
git push origin main
```

Expected: `main` pushed.
