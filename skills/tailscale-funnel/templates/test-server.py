#!/usr/bin/env python3
"""Tailscale Funnel 测试 Web 服务

一个简单的 HTTP 服务，展示来访请求的详细信息，
方便验证 Tailscale Funnel / 内网穿透是否正常工作。

Usage:
    python3 test-server.py              # 监听 :8765
    PORT=3000 python3 test-server.py    # 自定义端口

通过 Funnel 暴露后，访问 / 返回 HTML 页面，/api 返回 JSON。
"""

import http.server
import json
import os
import socket
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8765))
START_TIME = time.time()

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #e0e0e0;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.container { max-width: 700px; width: 100%; }
.card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px; padding: 32px; margin-bottom: 20px;
  backdrop-filter: blur(10px);
}
h1 { font-size: 28px; margin-bottom: 8px; color: #7cff9e; }
.subtitle { color: #888; font-size: 14px; margin-bottom: 24px; }
.status-badge {
  display: inline-block; padding: 4px 14px;
  border-radius: 20px; font-size: 13px; font-weight: 600;
}
.status-ok { background: rgba(124,255,158,0.2); color: #7cff9e; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
.info-item { padding: 12px; background: rgba(255,255,255,0.04); border-radius: 8px; }
.info-label {
  font-size: 11px; color: #888; text-transform: uppercase;
  letter-spacing: 1px; margin-bottom: 4px;
}
.info-value {
  font-size: 15px; word-break: break-all;
  font-family: 'SF Mono', 'Fira Code', monospace; color: #a0d2ff;
}
.headers { margin-top: 16px; font-size: 13px; }
.header-row {
  padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
  display: flex; gap: 12px;
}
.header-key { color: #888; min-width: 140px; flex-shrink: 0; }
.header-val { color: #a0d2ff; word-break: break-all; }
.footer { text-align: center; color: #555; font-size: 12px; margin-top: 16px; }
"""


def uptime():
    s = int(time.time() - START_TIME)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}m {s}s"
    elif m > 0: return f"{m}m {s}s"
    return f"{s}s"


def render_html(client_ip, source_port, method, path, headers, body):
    header_rows = ""
    for k, v in sorted(headers.items()):
        header_rows += f'<div class="header-row"><span class="header-key">{k}</span><span class="header-val">{v}</span></div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tailscale Funnel 测试</title>
  <style>{CSS}</style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>🎉 穿透成功！</h1>
    <p class="subtitle">Tailscale Funnel 内网穿透测试页</p>
    <span class="status-badge status-ok">● 服务运行中</span>
  </div>
  <div class="card">
    <h2>📋 请求信息</h2>
    <div class="info-grid">
      <div class="info-item">
        <div class="info-label">客户端 IP</div>
        <div class="info-value">{client_ip}</div>
      </div>
      <div class="info-item">
        <div class="info-label">访问端口</div>
        <div class="info-value">{source_port}</div>
      </div>
      <div class="info-item">
        <div class="info-label">请求方法</div>
        <div class="info-value">{method}</div>
      </div>
      <div class="info-item">
        <div class="info-label">请求路径</div>
        <div class="info-value">{path}</div>
      </div>
      <div class="info-item">
        <div class="info-label">访问时间</div>
        <div class="info-value">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
      </div>
      <div class="info-item">
        <div class="info-label">服务运行时间</div>
        <div class="info-value">{uptime()}</div>
      </div>
    </div>
    <h2 style="margin-top:20px;">📨 请求头</h2>
    <div class="headers">{header_rows}</div>
    {f'<h2 style="margin-top:20px;">📝 请求体</h2><pre style="background:rgba(255,255,255,0.04);padding:12px;border-radius:8px;overflow-x:auto;font-size:13px;">{body}</pre>' if body else ''}
  </div>
  <p class="footer">🚀 通过 Tailscale Funnel 提供服务 | {socket.gethostname()}</p>
</div>
</body>
</html>"""


def render_json(client_ip, source_port, method, path, headers, body):
    return json.dumps(
        {
            "status": "ok",
            "message": "Tailscale Funnel 穿透成功!",
            "server": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(time.time() - START_TIME),
            "request": {
                "client_ip": client_ip,
                "source_port": source_port,
                "method": method,
                "path": path,
                "headers": headers,
                "body": body,
            },
        },
        indent=2,
        ensure_ascii=False,
    )


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_HEAD(self):
        self._handle()

    def _handle(self):
        body = ""
        if self.command in ("POST", "PUT"):
            length = int(self.headers.get("Content-Length", 0))
            if length > 0 and length < 1024 * 1024:
                body = self.rfile.read(length).decode("utf-8", errors="replace")

        client_ip, client_port = self.client_address
        headers = dict(self.headers)

        logger.info("%s %s from %s:%s", self.command, self.path, client_ip, client_port)

        accept = self.headers.get("Accept", "")
        if "application/json" in accept or self.path.startswith("/api"):
            content = render_json(client_ip, client_port, self.command, self.path, headers, body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(content.encode("utf-8")))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            content = render_html(client_ip, client_port, self.command, self.path, headers, body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(content.encode("utf-8")))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Use custom logger instead


if __name__ == "__main__":
    print("=" * 60)
    print("  Tailscale Funnel 测试 Web 服务")
    print("=" * 60)
    print(f"\n  监听端口: {PORT}")
    print(f"  本机地址: http://localhost:{PORT}")
    print(f"  主机名:   {socket.gethostname()}")
    print(f"\n  使用 Tailscale Funnel 暴露到公网:")
    print(f"    tailscale funnel --bg --set-path /test http://127.0.0.1:{PORT}")
    print(f"\n  停止服务: Ctrl+C")
    print("=" * 60)

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.shutdown()
