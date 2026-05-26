# Private Profile Template

Copy this template to:

```text
.private/server-profiles/<ssh-alias>.md
```

Keep `.private/` ignored by Git.

## Rules

- Do not include passwords.
- Do not include private keys.
- Do not include token values.
- Do not include full `.env` values.
- Do not include wallet files, cookies, or session values.
- Use aliases and high-level operational notes.

## Template

```markdown
# <ssh-alias> Server Profile

Last oriented: YYYY-MM-DD

## Connection

- SSH alias: <ssh-alias>
- Access method: SSH config
- Preferred user: configured locally

## System

- OS:
- Package manager:
- Reverse proxy:
- Process managers:
- Container runtime:

## Services

| Service | Manager | Path | Port | Public route | Notes |
| --- | --- | --- | --- | --- | --- |
| example | systemd | /opt/example | 3000 | example.com | no secrets |

## Conventions

- Project roots:
- Backup naming:
- Logs:
- Health checks:
- Deployment style:

## Known Risks

- 

## Open Questions

- 
```
