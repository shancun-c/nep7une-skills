---
name: tailscale-funnel
description: "Expose local web services to the public internet via Tailscale Funnel — deploy, configure, verify, switch between services, multi-path routing, and troubleshoot."
version: 1.0.0
author: agent
license: MIT
metadata:
  hermes:
    tags: [tailscale, funnel, tunnel, networking, deployment, web]
---

# Tailscale Funnel

Expose local web services to the public internet using Tailscale Funnel. Covers one-shot deployment, port switching, conflict resolution, and verification.

## Prerequisites

- Tailscale installed, authenticated, and running (`tailscale status`)
- **HTTPS certificates must be enabled** on the tailnet (required for Funnel)
- Funnel must be enabled in the Tailscale admin console

Verify readiness:
```bash
tailscale status                         # device should be online
tailscale funnel status                  # should NOT show "Funnel not available"
```

## Quick Deploy

```bash
# 1. Start your local service (e.g., on port 3000)
# 2. Expose it
tailscale funnel --bg 3000

# 3. Verify
tailscale funnel status
```

The public URL follows the pattern: `https://<hostname>.<tailnet>.ts.net`

Example: `https://nep7unemacbook-pro.tailbb09c2.ts.net/`

## Common Commands

```bash
tailscale funnel <port>                  # Foreground mode (blocking)
tailscale funnel --bg <port>             # Background mode (recommended)
tailscale funnel status                  # Show current config
tailscale funnel status --json           # Machine-readable
tailscale funnel reset                   # Remove all Funnel config
tailscale funnel --https=443 off         # Disable Funnel, keep serve rules
```

## Quick Deploy Workflow

Step-by-step from zero to public access:

```bash
# 1. Ensure Tailscale is running
tailscale status | head -1
# If "Tailscale is stopped.":
tailscale up --reset

# 2. Start your web server (bind to 0.0.0.0 so Funnel can reach it)
python3 server.py --host 0.0.0.0 --port 8765 &

# 3. Verify locally
curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8765/

# 4. Mount via Tailscale Funnel
tailscale funnel --bg --set-path /demo http://127.0.0.1:8765

# 5. Verify public access
curl -s -o /dev/null -w "HTTP %{http_code}" https://YOUR-DOMAIN.ts.net/demo
```

To remove a path later:
```bash
tailscale funnel --bg --set-path /demo off
```

## Multi-Path Routing

One Funnel domain can serve **many backend services** simultaneously via path-based routing. The mount path prefix is **stripped** before forwarding — a request to `/test/api` hits the backend as `/api`.

```bash
tailscale funnel reset   # Always start clean

# Mount multiple services at different paths
tailscale funnel --bg --set-path /       http://127.0.0.1:9119   # Primary (Dashboard)
tailscale funnel --bg --set-path /test   http://127.0.0.1:8765   # Test service
tailscale funnel --bg --set-path /api    http://127.0.0.1:3000   # API server

# Verify
tailscale funnel status
# Shows:
#   /       proxy http://127.0.0.1:9119
#   /test   proxy http://127.0.0.1:8765
#   /api    proxy http://127.0.0.1:3000
```

**Path stripping behavior:** The backend receives the URL with the mount prefix removed. `/test/some-page` → forwarded as `/some-page`. Test it with a service that echoes the request path to confirm.

**No per-service restart needed:** Adding a new path does not interrupt existing ones. The Funnel config is updated atomically.

## Switching Services (Port Changes)

When you need to move Funnel from one local port to another:

```bash
# 1. Reset existing config
tailscale funnel reset

# 2. Reconfigure with new port
tailscale funnel --bg <new_port>

# 3. Verify
tailscale funnel status
```

Do NOT try `tailscale funnel --bg <new_port>` while another Funnel is active — it will fail with "foreground listener already exists for port 443".

## Pitfalls

### Path collision with application routes

**Symptom:** After setting `--set-path /test → 8765`, a React app on `/` has a broken `/test` route, missing `/test.js` static asset, or a `/testing` page that returns the wrong content.

**Cause:** Funnel's path routing is **prefix matching with first-match priority**. Once `/test` is bound, *every* request starting with `/test` is forwarded to the bound backend — including `/test.js`, `/testing`, `/test/user`, and any SPA route under `/test`. The main app never sees these requests.

**Fix:** Use namespaced, non-colliding prefixes:
```bash
# Safe — namespaced, unlikely to collide with app routes
tailscale funnel --bg --set-path /__demo__     http://127.0.0.1:8765
tailscale funnel --bg --set-path /funnel-test  http://127.0.0.1:8765
tailscale funnel --bg --set-path /~status      http://127.0.0.1:3000
tailscale funnel --bg --set-path /svc/metrics  http://127.0.0.1:9090

# Risky — common words likely collide
tailscale funnel --bg --set-path /test   http://127.0.0.1:8765
tailscale funnel --bg --set-path /api    http://127.0.0.1:3000
tailscale funnel --bg --set-path /docs   http://127.0.0.1:8080
```

**Design rule:** Choose prefixes the target application would never use as route paths. Dashes and underscores (`/funnel-test`, `/svc_health`) are safer than short common words.

### Root path left unbound (by design)

If no service is bound to `/`, Funnel returns **HTTP 404** on the root URL. This is a valid security posture — random visitors scanning the domain see nothing. Only explicitly exposed paths are reachable.

### "foreground listener already exists for port 443"

**Symptom:**
```
Error: sending serve config: updating config: foreground listener already exists for port 443
```

**Cause:** A foreground Funnel (or `tailscale serve`) is already bound to port 443, often left from a previous session or a stale `tailscale serve` config.

**Fix:**
```bash
tailscale funnel reset      # Reset all Funnel/serve state
tailscale funnel --bg <port>  # Reconfigure fresh
```

### "Funnel not available" / HTTPS Required

Funnel requires HTTPS certificates enabled on the tailnet. Check the Tailscale admin console → DNS → HTTPS Certificates.

### Service not responding through Funnel

1. **Local first**: `curl http://localhost:<port>` — confirm the service runs locally
2. **Funnel status**: `tailscale funnel status` — confirm it points to the right port
3. **Tailscale status**: `tailscale status` — device must be online
4. **HTTPS certs**: Must be issued; check `tailscale cert` output
5. **Host header rejection**: Some apps (FastAPI with `TrustedHostMiddleware`, Hermes Dashboard) reject requests with non-localhost Host headers. Funnel forwards with the Funnel domain as Host. Fix with `--host 0.0.0.0 --insecure` (Dashboard) or by allowing the Funnel domain in your app's allowed hosts.

### Hermes Dashboard: "Invalid Host header"

The Dashboard defaults to `--host 127.0.0.1` and rejects requests whose Host header doesn't match (e.g., the Funnel domain). Fix:

```bash
hermes dashboard --stop                          # Kill existing instances
hermes dashboard --port 9119 --host 0.0.0.0 \    # Restart allowing external Host headers
  --insecure --no-open
```

The `--insecure` flag acknowledges the security trade-off. Since Funnel provides TLS termination, the local connection stays loopback-safe.

**Dashboard commands reference:**

| Command | Purpose |
|---------|---------|
| `hermes dashboard --port 9119` | Start (127.0.0.1 only) |
| `hermes dashboard --host 0.0.0.0 --insecure` | Start (accept external Host headers) |
| `hermes dashboard --stop` | Stop all running instances |
| `hermes dashboard --status` | List running instances |
| `hermes dashboard --tui` | Enable in-browser Chat tab |

### FastAPI/Starlette behind path-prefixed Funnel — broken static files and links

When Funnel mounts a service at a path prefix (e.g. `/trending` → `127.0.0.1:8000`), the backend receives requests without the prefix. Static file URLs like `/static/style.css` break because the browser resolves them against the domain root, not the prefix. Internal links (`/`, `/archive`) break the same way.

**Symptoms:**
- Page loads but CSS is missing (browser requests `/static/style.css` instead of `/trending/static/style.css`)
- Navigation links point to wrong URLs

**Fix — two changes required:**

1. **In templates**: Use `url_for` instead of hardcoded paths:
   ```html
   <!-- WRONG: breaks behind path-prefixed proxy -->
   <link rel="stylesheet" href="/static/style.css">
   <a href="/">Home</a>

   <!-- RIGHT: url_for generates prefix-aware URLs -->
   <link rel="stylesheet" href="{{ url_for('static', path='style.css') }}">
   <a href="{{ url_for('index') }}">Home</a>
   ```

2. **On the server**: Pass `--root-path` matching the Funnel path so `url_for` generates correct prefixed URLs:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --root-path /trending
   ```
   Without `--root-path`, `url_for('static', ...)` generates `/static/style.css` (broken). With it, generates `/trending/static/style.css` (correct).

**Verification**: `curl -s https://DOMAIN.ts.net/PREFIX/ | grep -o 'href="[^"]*"'` — all URLs should contain the prefix.

### Port already in use

Check what's listening:
```bash
lsof -i :<port>
```

Kill the old process if needed:
```bash
kill <pid>
```

## Verification

```bash
# From the local machine
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://<your-url>.ts.net/

# From an external network (mobile hotspot, different WiFi, friend's device)
# Just open the URL in a browser
```

## Service Lifecycle

Funnel runs in the background and survives terminal close. To stop permanently:

```bash
tailscale funnel --https=443 off
```

To restart after reboot, just re-run `tailscale funnel --bg <port>` — the config persists.

## Test Web Service

A reusable test server is available at **`templates/test-server.py`** — zero-dependency Python HTTP server that displays request details (client IP, headers, path, timestamp) in both HTML and JSON formats. Copy and run to verify Funnel routing:

```bash
python3 templates/test-server.py              # listens on :8765
PORT=3000 python3 templates/test-server.py    # custom port
```

The server responds with:
- **`GET /`** → HTML page showing client IP, headers, timestamp, server uptime
- **`GET /api`** → JSON with same detail (also responds when `Accept: application/json`)

After starting, expose it through Funnel at a specific path:
```bash
tailscale funnel --bg --set-path /test http://127.0.0.1:8765
```

Then verify from an external network — the page should show the public client IP, confirming traffic is coming through the Funnel.

## Related

- Tailscale docs: https://tailscale.com/kb/1247/funnel-serve-use-cases
- `tailscale serve` (internal-only, no public exposure): same syntax, no HTTPS requirement
- **`references/hermes-dashboard.md`** — Deploying Hermes Dashboard behind Funnel (startup commands, Host header fix, multi-path)
- **`templates/test-server.py`** — Reusable test HTTP server for verifying Funnel connectivity
