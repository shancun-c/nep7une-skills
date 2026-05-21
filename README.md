# nep7une-skills

Personal AgentSkills collection maintained by nep7une.

This repository is a skills collection, not a single skill folder. Each installable source skill lives under `skills/<skill-name>/` and contains its own `SKILL.md`.

Runtime installers place skills under a collection namespace:

```text
<runtime-skills-root>/nep7une-skills/<skill-name>
```

## Available Skills

| Skill | Path | Purpose |
| --- | --- | --- |
| `obsidian-wiki-skill` | `skills/obsidian-wiki-skill/` | Maintain and evolve Obsidian-based knowledge vaults with `orient`, `answer`, `ingest`, and `audit` workflows. |

## Repository Layout

```text
.
├── README.md
├── registry.yaml
├── installers/
│   ├── install-codex.sh
│   ├── install-hermes.sh
│   └── install-openclaw.sh
├── skills/
│   └── obsidian-wiki-skill/
│       ├── SKILL.md
│       ├── agents/
│       └── references/
└── docs/
    ├── obsidian-wiki-skill/
    └── superpowers/
```

## Install

Clone the collection:

```bash
git clone https://github.com/shancun-c/nep7une-skills.git
cd nep7une-skills
```

### Codex

Install all currently supported Codex skills:

```bash
./installers/install-codex.sh
```

Install one skill:

```bash
./installers/install-codex.sh --skill obsidian-wiki-skill
```

The default target is:

```text
~/.codex/skills/nep7une-skills/obsidian-wiki-skill
```

### Hermes

Hermes can use this repository as a custom skill tap:

```bash
hermes skills tap add shancun-c/nep7une-skills
hermes skills install shancun-c/nep7une-skills/obsidian-wiki-skill
```

For a local filesystem install:

```bash
./installers/install-hermes.sh
```

The default target is:

```text
~/.hermes/skills/nep7une-skills/obsidian-wiki-skill
```

### OpenClaw

Install into an OpenClaw workspace:

```bash
./installers/install-openclaw.sh --target /path/to/openclaw/workspace
```

This writes the skill to:

```text
/path/to/openclaw/workspace/skills/nep7une-skills/obsidian-wiki-skill
```

You can also install into a custom skills root:

```bash
./installers/install-openclaw.sh --skills-dir /path/to/skills
```

## Dry Run

All installer scripts support `--dry-run`:

```bash
./installers/install-codex.sh --dry-run
./installers/install-hermes.sh --dry-run
./installers/install-openclaw.sh --target /tmp/openclaw-workspace --dry-run
```

## Validate

Validate an individual skill with the Codex skill validator:

```bash
PYTHONPATH=.vendor/python \
python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/obsidian-wiki-skill
```

Expected output:

```text
Skill is valid!
```

## Obsidian Wiki Skill

`obsidian-wiki-skill` is a vault-aware knowledge maintenance skill for Obsidian-based Markdown systems.

It turns the LLM Wiki idea into a practical workflow for real Obsidian vaults. Instead of assuming a fixed wiki folder structure, it starts by understanding the user's existing vault and then works through four modes:

- `orient`: understand the vault before acting
- `answer`: answer from vault context without writing by default
- `ingest`: add new source material and selectively promote durable knowledge
- `audit`: review structure, navigation, metadata, relationships, and evidence quality

Inside `audit`, use `lint` as the default read-first health-check path.

### Companion Skills

This skill is an orchestration layer. It uses whatever Obsidian execution companions are available in the host runtime.

Codex companions:

- `obsidian-markdown`
- `obsidian-cli`
- `obsidian-bases`
- `json-canvas`

Hermes or other AgentSkills runtimes:

- `obsidian`, when available
- equivalent filesystem, Markdown, search, canvas, and structured-data tools

Recommended:

- `defuddle`

Optional:

- `anysearch`

These companion skills may come from the public [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) ecosystem or from an environment that already bundles them.

### Example Prompts

- `Use $obsidian-wiki-skill to orient to my Obsidian vault before we make changes.`
- `Use $obsidian-wiki-skill to ingest this article into my source and knowledge notes.`
- `Use $obsidian-wiki-skill to audit my vault for weak evidence and navigation drift.`
- `Use $obsidian-wiki-skill to lint my Obsidian vault and report broken structure, weak evidence, and index drift.`
- `Use $obsidian-wiki-skill with anysearch to fresh-check this stale knowledge note before updating it.`
- `Use $obsidian-wiki-skill to answer this question from my vault without writing back.`

## Development Notes

- Canonical skill source lives under `skills/`.
- Historical and design documents live under `docs/`.
- Runtime installs should copy only the relevant skill directory, not the whole repository.
- Keep `name: obsidian-wiki-skill` stable so existing invocations continue to work.
