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
| `server-ops-skill` | `skills/server-ops-skill/` | Safely operate SSH-accessible Linux servers with orientation, inspection, deployment, repair, rollback, and hardening workflows. |

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
│   ├── obsidian-wiki-skill/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   └── references/
│   └── server-ops-skill/
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
./installers/install-codex.sh --skill server-ops-skill
```

The default target is:

```text
~/.codex/skills/nep7une-skills/<skill-name>
```

### Hermes

Hermes can use this repository as a custom skill tap:

```bash
hermes skills tap add shancun-c/nep7une-skills
hermes skills install shancun-c/nep7une-skills/obsidian-wiki-skill
hermes skills install shancun-c/nep7une-skills/server-ops-skill
```

For a local filesystem install:

```bash
./installers/install-hermes.sh
```

The default target is:

```text
~/.hermes/skills/nep7une-skills/<skill-name>
```

### OpenClaw

Install into an OpenClaw workspace:

```bash
./installers/install-openclaw.sh --target /path/to/openclaw/workspace
```

This writes the skill to:

```text
/path/to/openclaw/workspace/skills/nep7une-skills/<skill-name>
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

## Dependency Checks

Installer scripts check skill dependencies by default before copying files.

Dependency levels:

- `required`: missing dependencies stop the install.
- `recommended`: missing dependencies are reported but do not stop the install.
- `optional`: missing dependencies are reported but do not stop the install.

Skip dependency checks when you are intentionally bootstrapping a runtime:

```bash
./installers/install-codex.sh --skip-deps
./installers/install-hermes.sh --skip-deps
./installers/install-openclaw.sh --target /path/to/openclaw/workspace --skip-deps
```

For `obsidian-wiki-skill`, Codex expects `obsidian-markdown`, `obsidian-cli`, `obsidian-bases`, and `json-canvas` as required companions. Hermes and OpenClaw expect an `obsidian` execution skill as the required baseline. `defuddle` is recommended, and `anysearch` is optional.

For `server-ops-skill`, the runtime dependency is the local `ssh` command plus a configured SSH alias. `rsync`, `scp`, and `ssh-keygen` are recommended local tools for deployment and key management workflows.

## Validate

Validate an individual skill with the Codex skill validator:

```bash
PYTHONPATH=.vendor/python \
python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/obsidian-wiki-skill
python3 /Users/wenweikun/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/server-ops-skill
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

## Server Ops Skill

`server-ops-skill` is a safe SSH operations skill for Linux servers.

It is designed for:

- orienting to a remote server before taking action
- inspecting systemd, Nginx, Docker, PM2, Node, Python, TLS, logs, ports, and project directories
- planning deployments and rollbacks
- repairing services with observe-first discipline
- proposing hardening steps without silently changing access controls

The skill defaults to an SSH alias named `nep7une-tokyo`, but the actual host, user, key, and authentication method must live in local private SSH configuration. Do not commit server credentials or private profiles to this repository.

Local server profiles belong under ignored paths such as:

```text
.private/server-profiles/<ssh-alias>.md
```

Example prompts:

- `Use $server-ops-skill to orient to nep7une-tokyo without making changes.`
- `Use $server-ops-skill to inspect why my Nginx route is returning 502.`
- `Use $server-ops-skill to plan a deployment for this Node service.`
- `Use $server-ops-skill to roll back the last service change safely.`

## Development Notes

- Canonical skill source lives under `skills/`.
- Historical and design documents live under `docs/`.
- Runtime installs should copy only the relevant skill directory, not the whole repository.
- Keep skill `name` values stable so existing invocations continue to work.
