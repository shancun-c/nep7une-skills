# Obsidian Wiki Skill

A vault-aware knowledge maintenance skill for Obsidian-based Markdown systems.

This project turns the LLM Wiki idea into a more practical skill for real Obsidian vaults. Instead of assuming a fixed wiki folder structure, it starts by understanding the user's existing vault and then works through four modes: `orient`, `answer`, `ingest`, and `audit`, with `lint` as a built-in sub-mode under `audit`.

## Why This Exists

The original `llm-wiki` pattern is strong on the core idea of persistent, compounding knowledge. In practice, many Obsidian users already have their own vault structure, templates, indexes, and note taxonomy. A good skill should adapt to that reality instead of forcing a brand-new information architecture.

This skill is designed to:

- respect existing vault structure and naming habits
- treat Obsidian as the host environment
- distinguish source preservation from knowledge synthesis
- avoid silently promoting chat answers into stable vault knowledge
- add stronger evidence, safety, and write-discipline rules
- route low-level execution to dedicated Obsidian companion skills

## What The Skill Does

This skill acts as an orchestration layer for Obsidian knowledge work.

It decides:

- what mode the current request belongs to
- whether the task should remain read-only or become a write workflow
- which note layer should receive new information
- which Obsidian companion skill should perform the concrete operation

It does not try to replace low-level Obsidian syntax or CLI skills.

## Core Modes

- `orient`: understand the vault before acting
- `answer`: answer from vault context without writing by default
- `ingest`: add new source material and selectively promote durable knowledge
- `audit`: review structure, navigation, metadata, relationships, and evidence quality

Inside `audit`, use `lint` as the default read-first health-check path.

## Design Principles

- Host-first: read the existing vault before making assumptions
- Role-first: infer note roles from `type`, purpose, templates, and relationships rather than folder names alone
- Conservative by default: keep `orient` and `answer` read-only
- Evidence-aware: treat source notes as the evidence layer and knowledge notes as the conclusion layer
- Write-safe: require planning for medium-risk writes and confirmation for high-risk writes
- Companion-skill driven: use dedicated Obsidian skills for concrete format and vault actions
- Log-aware: treat `log.md` as an active maintenance log that can be rotated and archived over time
- Search-aware: optionally use AnySearch for fresh-checks, source discovery, vertical search, and evidence-gap investigation

## Required Companion Skills

This skill depends on the following execution-layer skills:

- `obsidian-markdown`
- `obsidian-cli`
- `obsidian-bases`
- `json-canvas`

Recommended:

- `defuddle`

If those skills are unavailable, this skill should not pretend to offer complete Obsidian-native behavior.

These companion skills come from the Obsidian skill ecosystem, such as the public [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) repository or an environment that already bundles them.

## Repository Layout

```text
.
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── references/
│   ├── workflow-modes.md
│   ├── evidence-and-safety.md
│   └── companion-skill-routing.md
└── docs/
    ├── SKILL.md
    ├── karpathy-llm-wiki.md
    ├── upgrade.md
    └── superpowers/
```

## Key Files

- [SKILL.md](SKILL.md): the actual skill definition
- [agents/openai.yaml](agents/openai.yaml): UI metadata for the skill
- [references/workflow-modes.md](references/workflow-modes.md): detailed behavior for `orient`, `answer`, `ingest`, and `audit`
- [references/evidence-and-safety.md](references/evidence-and-safety.md): evidence policy, source trust, conflict handling, and write safety
- [references/log-maintenance.md](references/log-maintenance.md): how to keep `log.md` useful as it grows
- [references/companion-skill-routing.md](references/companion-skill-routing.md): when to invoke each companion Obsidian skill
- [docs/SKILL.md](docs/SKILL.md): original upstream skill used as a baseline
- [docs/karpathy-llm-wiki.md](docs/karpathy-llm-wiki.md): the core idea document
- [docs/upgrade.md](docs/upgrade.md): analysis of what needed to change

## Installation

This repository is already the final skill folder. You do not need to generate or rearrange anything before installing it.

### Prerequisites

Before using this skill, make sure your environment already has these companion skills available:

- `obsidian-markdown`
- `obsidian-cli`
- `obsidian-bases`
- `json-canvas`

Recommended:

- `defuddle`
- `anysearch`

If your environment does not bundle them by default, install them from your Obsidian skills source first.

### Install From GitHub

Clone the repository:

```bash
git clone https://github.com/shancun-c/obsidian-wiki-skill.git
cd obsidian-wiki-skill
```

Then place the folder where Codex can discover skills:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$(pwd)" "${CODEX_HOME:-$HOME/.codex}/skills/obsidian-wiki-skill"
```

Or copy the folder directly:

```bash
cp -R /path/to/obsidian-wiki-skill "${CODEX_HOME:-$HOME/.codex}/skills/obsidian-wiki-skill"
```

### Verify Installation

After installation, the target folder should contain at least:

```text
obsidian-wiki-skill/
├── SKILL.md
├── agents/openai.yaml
└── references/
```

If those files are present and the companion skills are available, the skill is ready to use.

### Optional AnySearch Setup

AnySearch is optional. The skill works without it, but AnySearch can improve current-event checks, vertical search, batch source discovery, and evidence-gap investigations.

Install the AnySearch skill separately if your environment supports companion skills:

```bash
git clone https://github.com/anysearch-ai/anysearch-skill.git /path/to/anysearch
```

AnySearch supports anonymous access with lower rate limits. For higher limits, configure `ANYSEARCH_API_KEY` following the AnySearch skill's own README.

## Usage

Use this skill when you want Codex to work inside an existing Obsidian vault as a knowledge maintainer rather than a generic editor.

### Typical Workflow

1. Open a task that references your Obsidian vault.
2. Invoke `$obsidian-wiki-skill`.
3. Let it orient to the vault first.
4. Continue into `answer`, `ingest`, or `audit` depending on the task.

Example prompts:

- `Use $obsidian-wiki-skill to orient to my Obsidian vault before we make changes.`
- `Use $obsidian-wiki-skill to ingest this article into my source and knowledge notes.`
- `Use $obsidian-wiki-skill to audit my vault for weak evidence and navigation drift.`
- `Use $obsidian-wiki-skill to lint my Obsidian vault and report broken structure, weak evidence, and index drift.`
- `Use $obsidian-wiki-skill with anysearch to fresh-check this stale knowledge note before updating it.`
- `Use $obsidian-wiki-skill to answer this question from my vault without writing back.`

## Validation

The skill was validated with the `skill-creator` quick validator.

If you want to re-run validation locally:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/obsidian-wiki-skill
```

If your Python environment does not already include `PyYAML`, install it first or provide it through `PYTHONPATH`.

## Status

This is an initial public version focused on:

- host-aware Obsidian orientation
- safe source ingest
- conservative answer behavior
- evidence and write-discipline rules
- strong composition with Obsidian companion skills

Future iterations can add helper scripts, forward tests, and more opinionated audit automation if repeated workflows justify them.
