# Server Orientation

Use this workflow before acting on a new or stale server context.

## Preflight

1. Choose the SSH alias. Default to `nep7une-tokyo` when the user does not specify another alias.
2. Run `ssh -G <alias>` locally and confirm the alias resolves.
3. Look for `.private/server-profiles/<alias>.md`.
4. If the profile is missing or stale, run read-only orientation.

## Read-Only Inventory

Prefer commands like:

```bash
ssh <alias> 'whoami; hostnamectl; uptime; uname -a; cat /etc/os-release'
ssh <alias> 'free -h; df -hT; lsblk -f'
ssh <alias> 'ip -brief addr; ss -tulpen'
ssh <alias> 'systemctl --type=service --state=running --no-pager --no-legend'
ssh <alias> 'systemctl list-unit-files --type=service --state=enabled --no-pager --no-legend'
ssh <alias> 'systemctl list-timers --all --no-pager'
```

Probe tool availability:

```bash
ssh <alias> 'command -v nginx || true; command -v caddy || true; command -v apache2 || true; command -v docker || true; command -v pm2 || true; command -v node || true; command -v python3 || true; command -v git || true'
```

Probe likely project roots without reading secrets:

```bash
ssh <alias> 'find /srv /opt /var/www /home -maxdepth 3 -mindepth 1 -type d 2>/dev/null | sort | sed -n "1,200p"'
```

Avoid broad `/root` scans unless needed. If `/root` must be inspected, list names only and avoid reading secret-bearing files.

## Orientation Output

Summarize:

- OS and package manager
- active reverse proxy
- active process managers
- running services
- listening ports
- likely project directories
- backup conventions observed
- immediate risks or unknowns

Do not paste long inventories unless the user asks.
