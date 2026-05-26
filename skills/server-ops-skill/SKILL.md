---
name: server-ops-skill
description: Safely operate SSH-accessible Linux servers. Use when an agent needs to orient to a remote server, inspect running web services, diagnose incidents, manage systemd/Nginx/Docker/PM2/Node/Python services, deploy or update applications, plan rollbacks, or propose hardening steps through SSH without storing credentials in the skill.
---

# Server Ops Skill

## Mission

Use this skill for safe SSH-based server operations.

This skill is workflow-first. It helps the agent decide what to inspect, how to plan a change, when to ask for confirmation, and how to verify or roll back. It does not store credentials, private keys, passwords, `.env` values, or raw production secrets.

Default SSH alias:

```text
nep7une-tokyo
```

Treat this as a local alias only. The actual host, user, key, and authentication method must live in local SSH config or another private configuration outside the public skill.

## Private Profiles

Before server-specific work, look for a local private profile:

```text
.private/server-profiles/<ssh-alias>.md
```

Use it only as context. Never assume it is complete or current. If it is missing or stale, run `orient`.

Private profiles may contain sanitized operational facts, but must not contain credentials, private keys, token values, full `.env` values, session files, wallets, cookies, or raw secrets.

See [private-profile-template.md](references/private-profile-template.md).

## Modes

### `orient`

Use for a new server, stale context, or before unfamiliar work.

Default behavior:

- read-only
- verify SSH alias resolution
- inspect OS, uptime, resources, disks, ports, process managers, reverse proxies, enabled services, timers, likely project roots, and deployment conventions
- avoid reading secrets

Read [server-orientation.md](references/server-orientation.md).

### `inspect`

Use when the user asks about a service, domain, port, process, log, certificate, reverse proxy route, or deployment target.

Default behavior:

- read-only
- target the smallest useful set of commands
- inspect service state, logs, routes, ports, project directory, and health checks
- redact values that look like secrets

Read [service-operations.md](references/service-operations.md).

### `deploy`

Use when creating a new service or updating an existing one.

Default behavior:

- write-capable only after a deployment plan and user confirmation
- identify artifact, runtime, service manager, proxy route, port, persistence, logs, health check, backup, and rollback path
- stage before switching traffic
- validate after deployment

Read [deployment-workflow.md](references/deployment-workflow.md).

### `repair`

Use for broken services or incident response.

Default behavior:

- observe first, change second
- propose the smallest reversible fix
- require confirmation before restarts, config edits, package changes, firewall changes, or destructive commands

Read [service-operations.md](references/service-operations.md) and [ssh-safety.md](references/ssh-safety.md).

### `rollback`

Use to revert a deployment, config edit, service unit change, proxy route, or package change.

Default behavior:

- identify previous known-good state
- preserve the current failed state when practical
- require confirmation before changing the server
- verify route and service health after rollback

Read [deployment-workflow.md](references/deployment-workflow.md).

### `harden`

Use for security review and hardening.

Default behavior:

- report findings first
- treat SSH policy, firewall defaults, root login, public broker/admin ports, secret rotation, TLS changes, and unattended upgrades as high-impact
- require explicit confirmation before changing access controls

Read [ssh-safety.md](references/ssh-safety.md).

## Risk Rules

Low risk:

- read-only inspection commands
- status checks
- log reads with redaction
- config syntax tests

Medium risk, plan first:

- service restart
- package install
- artifact upload
- service-specific config edit
- new systemd unit
- reverse proxy route change

High risk, explicit confirmation required:

- SSH access policy changes
- firewall default changes
- stopping production services
- TLS certificate changes
- credential rotation
- database or broker state changes
- broad recursive file operations
- reboot
- delete, overwrite, or `rm -rf`

## Safety Defaults

- Prefer `ssh <alias> '<read-only command>'` for one-off checks.
- Avoid interactive sessions unless needed.
- Never embed passwords in commands.
- Never commit server facts that identify private infrastructure.
- Never print secrets back to the user.
- Do not read `.env` values unless the user explicitly asks.
- Before writing, state impact, exact commands, backup path, verification, and rollback.
- After writing, verify service state, logs, ports, routes, and health endpoint.

## Quick Routing

- SSH and credential safety: [ssh-safety.md](references/ssh-safety.md)
- New or stale server context: [server-orientation.md](references/server-orientation.md)
- Existing services, logs, proxies, ports: [service-operations.md](references/service-operations.md)
- Deployments and rollbacks: [deployment-workflow.md](references/deployment-workflow.md)
- Local private profile format: [private-profile-template.md](references/private-profile-template.md)
