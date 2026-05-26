# Deployment Workflow

Use this for `deploy` and `rollback`.

## Deployment Plan

Before writing to the server, produce a plan with:

- target SSH alias
- app name
- source artifact or repository
- runtime and package manager
- target directory
- service manager
- port and reverse proxy route
- environment variable handling
- data persistence
- logs
- backup path
- rollback path
- verification commands

Ask for confirmation before running write commands.

## Safe Deployment Shape

Prefer this sequence:

1. Build or package locally when possible.
2. Upload to a timestamped release directory.
3. Preserve existing config and `.env` files without printing values.
4. Install dependencies in the release directory.
5. Run local app checks or build checks.
6. Create or update a service config with a backup.
7. Test reverse proxy syntax.
8. Switch symlink or service target.
9. Restart or reload the smallest affected service.
10. Verify health, logs, ports, and route.

## Verification

Use a service-specific set of checks:

```bash
ssh <alias> 'systemctl is-active <service>'
ssh <alias> 'journalctl -u <service> -n 80 --no-pager'
ssh <alias> 'ss -tulpen | grep <port> || true'
ssh <alias> 'curl -fsS http://127.0.0.1:<port>/health || true'
curl -I https://<domain>
```

Only use external `curl` when the domain is public and the user expects public verification.

## Rollback

Before rollback:

- identify the last known-good release
- preserve current failing release if disk space allows
- restore service config or symlink
- test proxy config
- reload or restart the smallest affected service
- verify health

If rollback fails, stop and report the exact state instead of stacking more changes.

## Backups

Use timestamped backups:

```text
<file>.bak-YYYYMMDD-HHMMSS
<directory>.prev-YYYYMMDD-HHMMSS
```

Never overwrite a backup with the same name.
