# server-ops-skill Design

Date: 2026-05-26

## Goal

Create `server-ops-skill`, a public AgentSkills-compatible skill for safe SSH-based server operations.

The skill should help an agent orient to a remote Linux server, inspect running web services, deploy or update services, troubleshoot incidents, roll back changes, and propose hardening steps. It must not store credentials, private IP addresses, tokens, private keys, `.env` values, or sensitive service internals in the public repository.

## Security Model

The public skill is generic. Runtime-specific server details belong in local private configuration.

Public repository may contain:

- generic SSH operation rules
- safety checklists
- deployment and rollback workflows
- service inspection patterns for systemd, Nginx, Docker, PM2, Node, Python, and TLS certificates
- a sanitized private profile template

Public repository must not contain:

- passwords
- private keys
- token values
- `.env` contents
- exact production secrets
- root passwords
- sensitive operational logs
- private profile files

The user's server should be accessed through an SSH config alias. The initial alias is:

```text
nep7une-tokyo
```

The skill should refer to this as a default alias only. The actual `HostName`, `User`, `IdentityFile`, and authentication mechanism live in `~/.ssh/config` or another local private configuration source.

## Private Profile Policy

Use `.private/server-profiles/<alias>.md` for local-only server notes.

This folder must be ignored by Git. A private profile may include operational facts such as:

- server OS family and package manager
- known process managers
- known reverse proxies
- high-level service inventory
- deployment directories
- logging conventions
- rollback conventions

A private profile still must not include secrets or full environment variable values.

If a private profile is missing, the skill should run `orient` before taking action.

## Skill Layout

```text
skills/server-ops-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── ssh-safety.md
    ├── server-orientation.md
    ├── service-operations.md
    ├── deployment-workflow.md
    └── private-profile-template.md
```

Do not add a README inside the skill folder. Collection-level documentation belongs in the top-level `README.md`.

## Skill Modes

### `orient`

Use for a new server, stale context, or before unfamiliar operations.

Behavior:

- read-only by default
- check SSH alias resolution before connecting
- identify OS, uptime, disk, memory, package manager, open ports, process managers, reverse proxies, enabled services, timers, and likely project roots
- avoid reading secrets such as `.env`, private keys, tokens, wallet files, cookies, or session databases
- summarize findings as an operational map

### `inspect`

Use when the user asks about a specific service, domain, port, log, route, certificate, or deploy target.

Behavior:

- prefer targeted read-only commands
- inspect systemd state, process tree, listening ports, reverse proxy route, health endpoint, logs, and project directory
- redact values that look like credentials
- report uncertainty and next checks instead of guessing

### `deploy`

Use when creating a new service or updating an existing one.

Behavior:

- produce a deployment plan before changing the server
- identify runtime, service manager, reverse proxy, ports, persistence, logs, health checks, backups, and rollback path
- require explicit confirmation before writes
- stage artifacts safely before switching traffic
- validate service, logs, ports, reverse proxy config, TLS, and health endpoints after deployment

### `repair`

Use for incident response or broken services.

Behavior:

- observe first, change second
- collect symptoms, recent changes, logs, resource pressure, port conflicts, dependency failures, and proxy errors
- propose the smallest reversible fix
- require confirmation before restarts, package changes, config edits, firewall changes, or destructive commands

### `rollback`

Use when reverting a deployment, config edit, or service change.

Behavior:

- identify previous known-good artifact, config backup, unit file, and reverse proxy state
- preserve current broken state for postmortem when practical
- perform rollback only after confirmation
- verify service and route after rollback

### `harden`

Use for security review and hardening.

Behavior:

- provide findings and recommendations first
- treat SSH policy, firewall policy, root login, open broker ports, public admin ports, secret rotation, and unattended upgrades as high-impact changes
- require explicit confirmation before modifying access or firewall settings

## Risk Levels

Read-only commands are low risk.

Medium-risk operations require a short plan before execution:

- service restart
- package install or upgrade
- copying deployment artifacts
- editing a service-specific config
- adding a new systemd unit
- changing reverse proxy routes

High-risk operations require explicit user confirmation:

- changing SSH login policy
- changing firewall defaults
- stopping production services
- modifying TLS certificates
- deleting files or directories
- rotating credentials
- changing database or broker state
- running broad recursive commands
- rebooting the server

## Command Safety

The skill should prefer:

- `ssh <alias> '<read-only command>'` for one-off checks
- `systemctl status`, `systemctl show`, and `journalctl -u`
- `ss -tulpen` for ports
- `nginx -T` or equivalent proxy config dumps, with redaction
- `docker ps`, `docker compose ls`, and service-local compose inspection
- `pm2 list` and targeted `pm2 logs`

The skill should avoid:

- embedding passwords in commands
- writing temporary scripts that contain secrets
- reading `.env` values unless the user explicitly requests it
- printing secrets back to the user
- blind `rm -rf`
- blind `chmod -R` or `chown -R`
- unplanned `apt upgrade`
- direct production edits without backup

## Dependencies

Runtime dependencies:

- local `ssh` command
- configured SSH alias for target server

Recommended local tools:

- `rsync`
- `scp`
- `ssh-keygen`

No external network service dependency is required beyond SSH access to the user's server.

## Collection Integration

Add `server-ops-skill` to:

- top-level `README.md`
- `registry.yaml`
- collection installer dependency metadata

Runtime install paths should follow the collection namespace:

```text
~/.codex/skills/nep7une-skills/server-ops-skill
~/.hermes/skills/nep7une-skills/server-ops-skill
./skills/nep7une-skills/server-ops-skill
```

## Validation

Before completion:

- `quick_validate.py skills/server-ops-skill` passes
- `git grep` confirms no known password, private key, `.env` value, or raw server credential is committed
- installer dry-runs still work
- `registry.yaml` remains valid YAML
- `README.md` lists both skills
- `.private/` is ignored by Git

## Implementation Notes

The initial version should be workflow-first, not automation-heavy. Do not add deployment scripts until repeated real operations reveal stable patterns. This keeps the public skill useful across servers while avoiding premature automation against an evolving production host.
