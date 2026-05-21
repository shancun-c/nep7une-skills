# nep7une-skills Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current single-skill repository into a `nep7une-skills` collection that can batch-install `obsidian-wiki-skill` into Codex, Hermes, and OpenClaw-compatible skill folders.

**Architecture:** Keep `skills/obsidian-wiki-skill/` as the canonical skill source. Keep runtime-specific install behavior in small shell scripts under `installers/`. Keep historical design/source docs under `docs/obsidian-wiki-skill/` so runtime installs stay clean.

**Tech Stack:** Markdown AgentSkills format, POSIX shell scripts, Git/GitHub CLI, Codex `quick_validate.py`.

---

## File Map

- Move: `SKILL.md` -> `skills/obsidian-wiki-skill/SKILL.md`
- Move: `agents/openai.yaml` -> `skills/obsidian-wiki-skill/agents/openai.yaml`
- Move: `references/*` -> `skills/obsidian-wiki-skill/references/*`
- Move: `docs/SKILL.md` -> `docs/obsidian-wiki-skill/original-SKILL.md`
- Move: `docs/karpathy-llm-wiki.md` -> `docs/obsidian-wiki-skill/karpathy-llm-wiki.md`
- Move: `docs/upgrade.md` -> `docs/obsidian-wiki-skill/upgrade.md`
- Modify: `README.md` into collection-level documentation
- Create: `registry.yaml`
- Create: `installers/install-codex.sh`
- Create: `installers/install-hermes.sh`
- Create: `installers/install-openclaw.sh`
- Keep: `docs/superpowers/specs/2026-05-21-nep7une-skills-collection-design.md`

## Task 1: Restructure Repository

**Files:**
- Move: paths listed in File Map

- [ ] **Step 1: Create canonical directories**

Run:

```bash
mkdir -p skills/obsidian-wiki-skill docs/obsidian-wiki-skill installers
```

Expected: directories exist.

- [ ] **Step 2: Move skill runtime files**

Run:

```bash
git mv SKILL.md skills/obsidian-wiki-skill/SKILL.md
git mv agents skills/obsidian-wiki-skill/agents
git mv references skills/obsidian-wiki-skill/references
```

Expected: root no longer contains `SKILL.md`, `agents/`, or `references/`.

- [ ] **Step 3: Move Obsidian source docs**

Run:

```bash
git mv docs/SKILL.md docs/obsidian-wiki-skill/original-SKILL.md
git mv docs/karpathy-llm-wiki.md docs/obsidian-wiki-skill/karpathy-llm-wiki.md
git mv docs/upgrade.md docs/obsidian-wiki-skill/upgrade.md
```

Expected: source docs live under `docs/obsidian-wiki-skill/`.

## Task 2: Add Collection Metadata

**Files:**
- Create: `registry.yaml`
- Modify: `README.md`

- [ ] **Step 1: Write `registry.yaml`**

Create a registry with one skill:

```yaml
name: nep7une-skills
description: Personal AgentSkills collection maintained by nep7une.
repository: https://github.com/shancun-c/nep7une-skills
skills:
  - slug: obsidian-wiki-skill
    title: Obsidian Wiki Skill
    path: skills/obsidian-wiki-skill
    description: Maintain and evolve Obsidian-based knowledge vaults with orientation, ingest, answer, and audit workflows.
    runtimes:
      codex:
        install_path: ~/.codex/skills/nep7une-skills/obsidian-wiki-skill
      hermes:
        install_path: ~/.hermes/skills/nep7une-skills/obsidian-wiki-skill
      openclaw:
        install_path: ./skills/nep7une-skills/obsidian-wiki-skill
```

- [ ] **Step 2: Rewrite top-level README**

The README must describe the repository as a collection, list `obsidian-wiki-skill`, and include Codex, Hermes tap, Hermes local, and OpenClaw install commands.

## Task 3: Add Installer Scripts

**Files:**
- Create: `installers/install-codex.sh`
- Create: `installers/install-hermes.sh`
- Create: `installers/install-openclaw.sh`

- [ ] **Step 1: Implement shared script pattern**

Each script should:

- Resolve repo root from the script location.
- Default `SKILL_NAME=obsidian-wiki-skill`.
- Validate `skills/$SKILL_NAME/SKILL.md` exists.
- Print source and target.
- Support `--dry-run`.
- Use `rsync -a --delete` only inside the target skill directory.

- [ ] **Step 2: Make scripts executable**

Run:

```bash
chmod +x installers/install-codex.sh installers/install-hermes.sh installers/install-openclaw.sh
```

Expected: scripts are executable.

## Task 4: Validate and Sync

**Files:**
- Runtime target: `~/.codex/skills/nep7une-skills/obsidian-wiki-skill`
- Runtime target: `~/.hermes/skills/nep7une-skills/obsidian-wiki-skill`

- [ ] **Step 1: Validate canonical skill**

Run:

```bash
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/obsidian-wiki-skill
```

Expected: `Skill is valid!`

- [ ] **Step 2: Dry-run installer scripts**

Run:

```bash
installers/install-codex.sh --dry-run
installers/install-hermes.sh --dry-run
installers/install-openclaw.sh --target /tmp/openclaw-skills-test --dry-run
```

Expected: each script prints source and target without writing.

- [ ] **Step 3: Sync Codex and Hermes local installs**

Run:

```bash
installers/install-codex.sh
installers/install-hermes.sh
```

Expected: installed copies update from canonical skill source.

- [ ] **Step 4: Validate installed copies**

Run:

```bash
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/wenweikun/.codex/skills/nep7une-skills/obsidian-wiki-skill
PYTHONPATH=.vendor/python python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/wenweikun/.hermes/skills/nep7une-skills/obsidian-wiki-skill
```

Expected: both return `Skill is valid!`

## Task 5: Commit, Push, and Rename GitHub Repository

**Files:**
- Git repository metadata only

- [ ] **Step 1: Inspect status**

Run:

```bash
git status -sb
```

Expected: only intended migration files changed.

- [ ] **Step 2: Commit migration**

Run:

```bash
git add README.md registry.yaml installers skills docs
git commit --author="nep7une <nep7une@users.noreply.github.com>" -m "chore: convert repository to skills collection"
```

Expected: commit succeeds.

- [ ] **Step 3: Push current repository**

Run:

```bash
git push origin main
```

Expected: push succeeds.

- [ ] **Step 4: Rename GitHub repository**

Run:

```bash
gh repo rename nep7une-skills --repo shancun-c/obsidian-wiki-skill --yes
git remote set-url origin git@github.com:shancun-c/nep7une-skills.git
git remote -v
```

Expected: origin points to `git@github.com:shancun-c/nep7une-skills.git`.

- [ ] **Step 5: Push to renamed repository**

Run:

```bash
git push origin main
```

Expected: renamed remote receives `main`.

## Task 6: Final Verification

**Files:**
- Whole repository

- [ ] **Step 1: Confirm root is not a skill**

Run:

```bash
test ! -f SKILL.md
test -f skills/obsidian-wiki-skill/SKILL.md
```

Expected: both commands exit 0.

- [ ] **Step 2: Confirm README and registry mention new repository**

Run:

```bash
rg -n "nep7une-skills|obsidian-wiki-skill|hermes skills tap add|install-openclaw" README.md registry.yaml
```

Expected: all key terms appear.

- [ ] **Step 3: Confirm clean git state**

Run:

```bash
git status -sb
```

Expected: `## main...origin/main`.
