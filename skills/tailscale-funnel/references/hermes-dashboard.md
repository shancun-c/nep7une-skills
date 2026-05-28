# Hermes Dashboard via Tailscale Funnel
# Hermes Dashboard via Tailscale Funnel

Session reference: deploying the Hermes Agent Web Dashboard behind Tailscale Funnel on macOS.

## Hermes Dashboard Startup

The Hermes web UI is started via the `dashboard` CLI subcommand (NOT `web` — that was renamed):

```bash
cd ~/.hermes/hermes-agent
python -m hermes_cli.main dashboard --port 9119
```

- Backend: FastAPI on port 9119 (default)
- Frontend: Pre-built static SPA served from `hermes_cli/web_dist/`
- API endpoint: `http://localhost:9119/api/status` (health check)
The Dashboard reports:
- Hermes version and release date
- Gateway running state and PID
- Platform connection status (e.g., Feishu)
- Active session count
- Config/env paths

## Deployment to Funnel (Single Service)

```bash
# Start dashboard in background
cd ~/.hermes/hermes-agent && python -m hermes_cli.main dashboard --port 9119 &

# Expose via Funnel
tailscale funnel --bg 9119

# Result: https://<hostname>.<tailnet>.ts.net/
```

## Deployment to Funnel (Multi-Path, with other services)

```bash
hermes dashboard --port 9119 --host 0.0.0.0 --insecure --no-open &

tailscale funnel reset
tailscale funnel --bg --set-path /       http://127.0.0.1:9119  # Dashboard
tailscale funnel --bg --set-path /test   http://127.0.0.1:8765  # Test service
```

## Pitfall: "Invalid Host header"

**Symptom:** Browser shows "Invalid Host header. Dashboard requests must use the hostname the server was bound to."

**Cause:** Dashboard defaults to `--host 127.0.0.1` and validates the HTTP Host header. When accessed through Tailscale Funnel, the Host header is the Funnel domain (e.g., `nep7unemacbook-pro.tailbb09c2.ts.net`), which doesn't match `127.0.0.1`.

**Fix:** Use `--host 0.0.0.0 --insecure`:

```bash
# Stop existing instances first
hermes dashboard --stop

# Restart with external Host header support
hermes dashboard --port 9119 --host 0.0.0.0 --insecure --no-open
```

The `--insecure` flag is required — it acknowledges the security implication. Since Funnel provides TLS termination, the local connection stays on loopback, so the risk is minimal.

**Dashboard CLI reference:**

| Flag | Purpose |
|------|---------|
| `--port 9119` | Listen port (default) |
| `--host 127.0.0.1` | Default: localhost only, rejects external Host headers |
| `--host 0.0.0.0 --insecure` | Accept any Host header (required for Funnel) |
| `--no-open` | Don't open browser on start |
| `--tui` | Enable in-browser Chat tab |
| `--stop` | Stop all running dashboard processes |
| `--status` | List running dashboard processes |

## Pitfall: Stale Funnel Config

If a previous Funnel config points to a different port (e.g., port 3000 with no service running), the Funnel URL will return a connection error even though `tailscale funnel status` shows it as active. Always reset before reconfiguring:

```bash
tailscale funnel reset && tailscale funnel --bg <new_port>
```

## Frontend Build

The web frontend (`web/`) is a React + Vite + TypeScript app. It builds to `hermes_cli/web_dist/`. If changes are made to the frontend:

```bash
cd ~/.hermes/hermes-agent/web
npm run build
```

No restart of the dashboard backend is needed — it serves the static files from disk on each request.
