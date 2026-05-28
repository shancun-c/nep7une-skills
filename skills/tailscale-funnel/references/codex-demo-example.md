# Session Example: Codex CLI Demo → Tailscale Funnel

Full end-to-end flow from a Codex-generated web app to public deployment.

## 1. Codex generates the app

```bash
DEMO_DIR=$(mktemp -d)
cd "$DEMO_DIR" && git init
codex exec --full-auto 'Build a single-page web dashboard with dark theme, live clock, system status cards, Canvas particle background, Python server on port 8765' 2>&1
```

## 2. Move to permanent location

```bash
mkdir -p ~/demos/neonops-dashboard
cp "$DEMO_DIR"/index.html "$DEMO_DIR"/server.py "$DEMO_DIR"/README.md ~/demos/neonops-dashboard/
```

## 3. Start server on 0.0.0.0

```bash
cd ~/demos/neonops-dashboard
python3 server.py --host 0.0.0.0 --port 8765 &
```

## 4. Verify locally

```bash
curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8765/
curl -s http://127.0.0.1:8765/ | grep -o "<title>[^<]*</title>"
```

## 5. Expose via Tailscale Funnel

```bash
tailscale funnel --bg --set-path /neonops http://127.0.0.1:8765
```

## 6. Verify public access

```bash
curl -s -o /dev/null -w "HTTP %{http_code}" https://DOMAIN.ts.net/neonops
```

## 7. Clean up old paths

```bash
tailscale funnel --bg --set-path /old-path off
tailscale funnel status  # verify current state
```

## Result

```
https://nep7unemacbook-pro.tailbb09c2.ts.net
├── /hermes    → Hermes Dashboard (127.0.0.1:9119)
└── /neonops   → NeonOps Dashboard (127.0.0.1:8765)
```
