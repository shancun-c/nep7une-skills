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

## Install

Clone the collection:

```bash
git clone https://github.com/shancun-c/nep7une-skills.git
cd nep7une-skills
```

### Codex

Install the default Codex skill (`obsidian-wiki-skill`):

```bash
./installers/install-codex.sh
```

Install one skill:

```bash
./installers/install-codex.sh --skill knowledge-canvas-sync
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
hermes skills install shancun-c/nep7une-skills/knowledge-canvas-sync
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

## Knowledge Canvas Sync

`knowledge-canvas-sync` is a daily maintenance skill for Obsidian knowledge canvases.

It scans newly ingested source notes, extracts durable knowledge insights, creates or updates evergreen knowledge notes, and maintains a living visual knowledge graph in a `.canvas` file — with color-coded nodes (yellow=new, cyan=established, purple=foundational) and relationship edges.

Key features:

- Extracts knowledge across any domain — not limited to pre-defined groups
- Creates knowledge notes in `30 Knowledge/` with source traceability
- Maintains the canvas at `99 System/Knowledge Canvas.canvas`
- Includes `scripts/verify-canvas-colors.py` for post-write color validation
- Designed for cron integration (daily at 09:00)

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


## Safe installation and P0 regression checks

Installers require Python 3 and Bash. They no longer use `rsync --delete`.
A `--target` skill directory for Codex/Hermes must have the selected skill's name
as its final path component. Collection names and skill names must be simple
lowercase slugs; skills must appear in `registry.yaml`.

- Use `--dry-run` first: it validates and previews without creating files or locks.
- Stop the host runtime and editors before installing/updating. The lock only
  coordinates these installers, not arbitrary editors or sync clients.
- Fresh installs accept absent or empty dedicated directories. Existing nonempty
  directories need this installer's `.nep7une-install.json` ownership manifest.
  Older installations are deliberately not adopted automatically: install to a
  new dedicated directory, review/migrate your local configuration and state,
  then switch the runtime to it. Do not fabricate a marker to bypass the check.
- Managed files changed locally cause a refusal rather than silent overwrite.
  Unrelated files and the legacy `references/canvas-state.md` are retained.
  Obsolete package files are also retained: use a fresh directory for upgrades
  that require removing old files. This P0 patch does not implement pruning.
- Updates stage a full copy and retain a `SKILL-UUID` directory under
  `.nep7une-skill-backups` beside the configured skills root, outside skill discovery.
  A custom target on a different filesystem from this backup location is refused
  safely if the directory rename cannot cross filesystems. Existing file modes
  are preserved, including permission-only local edits.
  If interruption occurs between directory renames, inspect the backup and stage
  before restoring the previous directory. Do not delete a stale install lock
  until you have confirmed no installer is running. Backups may contain private
  local configuration: keep them private and remove them only after validation.
- Symlink paths/trees are refused. This conservative policy can reject otherwise
  legitimate linked home directories; use an explicit real directory instead.
- File snapshots detect changes during staging but cannot prevent a noncooperating
  process from changing files immediately after the final check. This is not a
  security boundary against a malicious local writer or a fully atomic multi-file
  transaction. Do not update while a runtime or sync client is modifying files.

Run the offline safety regression suite in a disposable checkout:

```bash
python3 -m unittest discover -s tests -v
for script in installers/*.sh; do bash -n "$script"; done
```

Tests use temporary directories and local toy Git remotes only. They do not
certify full Codex/Hermes/OpenClaw discovery or real Obsidian integration.
Dependency coverage and other P1 findings from the audit are separate follow-up
work; `--skip-deps` must not be taken as evidence that runtime dependencies exist.

### Integration check coverage

The offline suite also exercises all nine runtime/skill installer combinations
with synthetic dependency skills, repeated installation and byte comparisons.
Installed canvas repair/verify CLIs are exercised on disposable canvas files.
These checks validate packaging and command-line wiring, not real runtime skill
discovery or Obsidian behavior. Missing required Wiki dependencies are checked
for refusal. Knowledge Canvas dependency checks are matched against the registry for all three runtimes.
UTF-8 registry/manifest reads are explicit rather than dependent on host locale.
Native Windows/macOS execution remains unverified.

Knowledge Canvas requires `obsidian-canvas-creator` in every runtime, plus
`obsidian-markdown` in Codex or `obsidian` in Hermes. OpenClaw's additional
Obsidian/Markdown companions are recommended. These are presence checks only:
read each companion's instructions and verify compatible behavior before using
it. The repository does not supply, pin, or certify these external skills.
`json-canvas` may be installed for Wiki work but must not replace the mandatory
Canvas Creator workflow. Missing required companions stop installation;
recommended/optional gaps warn without blocking. `--skip-deps` explicitly bypasses
these checks and does not establish runtime readiness.
