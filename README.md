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
| `knowledge-canvas-sync` | `skills/knowledge-canvas-sync/` | Daily sync of Obsidian knowledge canvas — extract durable knowledge from source notes, maintain the visual knowledge graph, with color-verified canvas updates. |
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
│   ├── knowledge-canvas-sync/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── verify-canvas-colors.py
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

## Start here

This collection supplies instructions and helper scripts, not a running agent or
an Obsidian plugin. Installing it does **not** schedule jobs, configure SSH,
or grant permission to change a vault or server.

1. Read the [getting-started guide](docs/getting-started.md) for prerequisites,
   required companion skills, and runtime-specific target paths.
2. Try the [isolated examples](docs/examples.md) before using personal files.
3. Read [maintenance and recovery](docs/maintenance.md) before updating an
   existing installation. Stop the host runtime, editor, and sync client first.

The installers default to `obsidian-wiki-skill`; use `--skill` explicitly when
selecting a different skill. They require Bash and Python 3. Native Windows and
macOS execution and real runtime discovery remain unverified; Linux packaging
tests are not proof of support for those environments.

## Validate a checkout

From the repository root, run the offline tests and Bash syntax checks:

```bash
python3 -m unittest discover -s tests -v
for script in installers/*.sh; do bash -n "$script"; done
```

The tests use temporary files and toy local Git remotes. They do not install into
your runtime, access a real vault, or certify external companion behavior.

If you already have a Codex skill validator installed, its location varies by
installation. Use its actual local path and follow its dependency instructions;
this repository does not bundle or require that optional validator. Do not copy
another user's absolute path or assume `.vendor/python` exists here.

## Knowledge Canvas Sync

`knowledge-canvas-sync` is a daily maintenance skill for Obsidian knowledge canvases.

It scans newly ingested source notes, extracts durable knowledge insights, creates or updates evergreen knowledge notes, and maintains a living visual knowledge graph in a `.canvas` file — with color-coded nodes (yellow=new, cyan=established, purple=foundational) and relationship edges.

Key features:

- Extracts knowledge across any domain — not limited to pre-defined groups
- Creates knowledge notes in `30 Knowledge/` with source traceability
- Maintains the canvas at `99 System/Knowledge Canvas.canvas`
- Includes `scripts/verify-canvas-colors.py` for post-write color validation
- Can be invoked by a separately configured scheduler; installation creates no scheduled job

### Companion Skills

- `obsidian-canvas-creator` — required (canvas read/write, layout algorithms)
- `obsidian-markdown` — required for Codex (knowledge note creation)
- `obsidian-wiki-skill` — recommended (vault orientation)
- `json-canvas` is not a substitute for `obsidian-canvas-creator` in this workflow.
- `defuddle` — optional (web content extraction)
- `anysearch` — optional (cross-verification)

### Example Prompts

- `Load knowledge-canvas-sync skill, then run the full workflow: scan today's source notes, extract new knowledge, update canvas, report changes.`
- `Use knowledge-canvas-sync to scan my vault for new source notes and update the knowledge canvas.`
- `Use knowledge-canvas-sync to verify all canvas colors match the conventions.`

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


## Safety and validation boundaries

See [maintenance and recovery](docs/maintenance.md) for ownership checks,
backups, locally edited files, legacy installations, and concurrency limits.

The offline suite covers all nine runtime/skill installer combinations using
synthetic companion skills, repeated installation, byte comparisons, missing
required companions, and the installed Canvas helper CLIs. These are packaging
checks, **not** full Codex/Hermes/OpenClaw discovery or real Obsidian integration.
The installers check companion presence, not version or behavior compatibility.
`--skip-deps` bypasses those checks and never establishes runtime readiness.
