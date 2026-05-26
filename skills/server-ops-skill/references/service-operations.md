# Service Operations

Use this for `inspect`, `repair`, and post-deploy checks.

## systemd

Read-only checks:

```bash
ssh <alias> 'systemctl status <service> --no-pager'
ssh <alias> 'systemctl show <service> -p Id -p LoadState -p ActiveState -p SubState -p FragmentPath -p ExecStart -p WorkingDirectory -p EnvironmentFiles -p User -p Group --no-pager'
ssh <alias> 'journalctl -u <service> -n 120 --no-pager'
```

Before editing a unit:

- show the current unit path
- back up the unit file with a timestamp
- run `systemctl daemon-reload`
- restart only after confirmation
- verify with `systemctl is-active` and `journalctl`

## Reverse Proxies

Nginx checks:

```bash
ssh <alias> 'nginx -T 2>/dev/null | awk "/server_name|listen|proxy_pass|root |ssl_certificate/ { print }"'
ssh <alias> 'nginx -t'
```

Before changing Nginx:

- back up the site file
- test with `nginx -t`
- reload with `systemctl reload nginx`, not restart, when possible
- verify route with `curl -I`

## Ports and Processes

Use:

```bash
ssh <alias> 'ss -tulpen'
ssh <alias> 'ps -eo pid,ppid,user,stat,etime,cmd --sort=-etime | sed -n "1,80p"'
```

Report port conflicts by naming the process, unit, and expected owner.

## Docker

Read-only checks:

```bash
ssh <alias> 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"'
ssh <alias> 'docker compose ls'
```

Before changing containers:

- find the compose file
- identify volumes and networks
- preserve `.env` without printing values
- plan rollback to previous image or compose file

## PM2

Read-only checks:

```bash
ssh <alias> 'pm2 list'
ssh <alias> 'pm2 describe <name>'
ssh <alias> 'pm2 logs <name> --lines 120 --nostream'
```

Before changing PM2 apps:

- inspect the ecosystem file if present
- back up current process list with `pm2 save` only after confirmation
- verify app status and logs

## TLS

Read-only checks:

```bash
ssh <alias> 'certbot certificates 2>/dev/null || true'
ssh <alias> 'systemctl list-timers --all --no-pager | grep -i certbot || true'
```

Changing certificates is high risk. Ask for confirmation before issuance, renewal changes, or route changes.
