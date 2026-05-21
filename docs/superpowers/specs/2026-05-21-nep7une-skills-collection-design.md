# nep7une-skills Collection Design

Date: 2026-05-21

## Goal

Upgrade the current single-skill repository into `nep7une-skills`, a public skills collection that can be batch-installed into agent runtimes such as Hermes, OpenClaw, and Codex.

The existing `obsidian-wiki-skill` remains the first skill in the collection. Its skill name and installed runtime paths should remain stable so existing invocations like `$obsidian-wiki-skill` keep working.

## Recommended Architecture

Use a canonical `skills/<skill-name>/` layout:

```text
nep7une-skills/
├── README.md
├── registry.yaml
├── skills/
│   └── obsidian-wiki-skill/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       └── references/
├── docs/
│   └── obsidian-wiki-skill/
│       ├── original-SKILL.md
│       ├── karpathy-llm-wiki.md
│       └── upgrade.md
└── installers/
    ├── install-codex.sh
    ├── install-hermes.sh
    └── install-openclaw.sh
```

This layout matches Hermes tap expectations and stays compatible with OpenClaw-style workspace skill folders. The repository root becomes a collection, not a skill, so the root should not contain `SKILL.md` after migration.

## Layers

### Canonical Skill Layer

`skills/obsidian-wiki-skill/` is the single source of truth for the skill.

It contains only files needed by the skill runtime:

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- future `scripts/`, `assets/`, or `templates/` if genuinely required

The canonical skill should not include process docs, design notes, changelogs, or README clutter unless a runtime specifically needs them.

### Distribution Layer

`installers/` contains small scripts for copying or syncing selected skills into runtime-specific destinations.

Initial targets:

- Codex: `~/.codex/skills/nep7une-skills/<skill-name>`
- Hermes: `~/.hermes/skills/nep7une-skills/<skill-name>`
- OpenClaw: workspace-local `./skills/nep7une-skills/<skill-name>` or user-provided target directory

The scripts should accept a skill name or install all skills. They should avoid deleting unrelated user files outside the target skill directory.

`registry.yaml` records collection metadata and per-skill metadata for batch installers:

- skill slug
- title
- description
- default categories per runtime
- canonical path
- supported runtimes

### Documentation Layer

Top-level `README.md` explains the collection:

- what the repository contains
- available skills
- batch installation examples
- single-skill installation examples
- runtime compatibility notes

Skill-specific historical and design materials move under `docs/obsidian-wiki-skill/`. These files are not installed into runtime skill directories by default.

## Runtime Compatibility

### Hermes

Hermes custom taps use a GitHub repository with skills under `skills/` by default. Each skill directory must contain `SKILL.md`; supporting folders such as `references/`, `templates/`, `scripts/`, and `assets/` are installed alongside it.

The collection should therefore support:

```bash
hermes skills tap add shancun-c/nep7une-skills
hermes skills install shancun-c/nep7une-skills/obsidian-wiki-skill
```

The local installer copies the skill to `~/.hermes/skills/nep7une-skills/obsidian-wiki-skill` so collection-owned skills stay grouped together.

### OpenClaw

OpenClaw loads skills from workspace `skills/` directories and configured extra directories. The collection should therefore support copying selected skills into an OpenClaw workspace:

```bash
./installers/install-openclaw.sh --target /path/to/openclaw/workspace --skill obsidian-wiki-skill
```

Avoid OpenClaw-specific frontmatter until needed. Keep `name` and `description` stable and portable.

### Codex

Codex installs this collection under `~/.codex/skills/nep7une-skills/<skill-name>`. The Codex installer should sync from `skills/<skill-name>/` into that namespaced location.

## GitHub Changes

Rename the remote repository:

```text
shancun-c/obsidian-wiki-skill -> shancun-c/nep7une-skills
```

Update the local remote URL after GitHub rename:

```bash
git remote set-url origin git@github.com:shancun-c/nep7une-skills.git
```

Optionally rename the local checkout directory:

```text
/Users/wenweikun/workspace/project_obsidian-wiki-skill
-> /Users/wenweikun/workspace/project_nep7une-skills
```

This local directory rename is optional and can happen last.

## Migration Plan

1. Create `skills/obsidian-wiki-skill/`.
2. Move `SKILL.md`, `agents/`, and `references/` into `skills/obsidian-wiki-skill/`.
3. Move existing Obsidian-specific research docs into `docs/obsidian-wiki-skill/`.
4. Replace top-level README with a collection README.
5. Add `registry.yaml`.
6. Add installer scripts for Codex, Hermes, and OpenClaw.
7. Validate `skills/obsidian-wiki-skill/` with `quick_validate.py`.
8. Run installer scripts against Codex and Hermes local installs.
9. Commit and push.
10. Rename the GitHub repository to `nep7une-skills` and update `origin`.
11. Optionally rename the local checkout directory.

## Safety Requirements

- Do not change the skill's frontmatter `name: obsidian-wiki-skill`.
- Do not delete current Codex or Hermes installed copies until replacement sync succeeds.
- Do not install process docs into runtime skill directories.
- Keep external-search and vault-privacy guardrails intact.
- Installer scripts must not overwrite unrelated skills unless the target skill name matches.
- Installer scripts must support dry-run or clear output before destructive sync behavior.

## Validation

Before considering migration complete:

- `quick_validate.py skills/obsidian-wiki-skill` passes.
- Codex installed copy contains the migrated skill files.
- Hermes installed copy contains the migrated skill files under `~/.hermes/skills/nep7une-skills/`.
- Top-level README no longer presents the repository as a single skill.
- GitHub remote points to `shancun-c/nep7une-skills`.
- `git status -sb` is clean after commit and push.

## Open Questions Resolved

- The repository will use `skills/<skill-name>/`, not `research/<skill-name>/`, as its canonical layout.
- Runtime installs use the shared `nep7une-skills/<skill-name>` namespace instead of runtime-specific categories such as Hermes `research/`.
- `obsidian-wiki-skill` remains the installed skill name.
- The collection should optimize for batch installation while remaining manually inspectable and safe.
