#!/usr/bin/env python3
"""
mission-control - local, read-only project dashboard.

Serves index.html plus a merged JSON feed at /api/projects:
    static registry (projects.json)  +  live git status (.tools/repo_check.py --json)

Run:   python serve.py        (Windows)
       python3 serve.py       (macOS / Linux / Omarchy)
Then a browser opens at http://127.0.0.1:8787  -  Ctrl-C to stop.

No third-party dependencies. Needs Python 3.8+ and git on PATH.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
REPO_CHECK = HERE / ".tools" / "repo_check.py"
SCAN_ROOT = HERE.parent  # mission-control lives inside the projects root
REGISTRY = HERE / "projects.json"
INDEX = HERE / "index.html"

HOST = "127.0.0.1"
PORT = 8787


def load_registry() -> list[dict]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return data.get("projects", []) if isinstance(data, dict) else data


def run_repo_check(fetch: bool) -> tuple[list[dict], str]:
    """Return (live_results, error_message). Empty error means success."""
    if not REPO_CHECK.exists():
        return [], f"repo_check.py not found at {REPO_CHECK}"
    cmd = [sys.executable, str(REPO_CHECK), "--json", "--root", str(SCAN_ROOT)]
    if not fetch:
        cmd.append("--no-fetch")
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
    except subprocess.TimeoutExpired:
        return [], "repo_check.py timed out (try again or check the network)"
    except OSError as e:
        return [], f"could not run repo_check.py: {e}"
    # Exit code 1 just means "some repos need attention" - not a failure.
    try:
        return json.loads(proc.stdout), ""
    except json.JSONDecodeError:
        tail = (proc.stderr or proc.stdout or "no output").strip().splitlines()
        return [], "repo_check.py did not return JSON: " + (tail[-1] if tail else "?")


def build_payload(fetch: bool) -> dict:
    try:
        registry = load_registry()
        reg_error = ""
    except (OSError, json.JSONDecodeError) as e:
        registry, reg_error = [], f"could not read projects.json: {e}"

    live, live_error = run_repo_check(fetch)
    live_by_name = {r.get("name"): r for r in live}

    projects, seen = [], set()
    for p in registry:
        seen.add(p.get("name"))
        projects.append({**p, "git": live_by_name.get(p.get("name"))})

    # Repos that repo_check tracks but the registry hasn't mapped yet.
    for name, r in live_by_name.items():
        if name not in seen:
            projects.append({
                "name": name, "title": name, "lifecycle": "", "handover": "review",
                "summary": "Tracked by repo_check but not in the registry yet.",
                "tech": [], "url": "", "host": "", "repo": name,
                "contact": "", "creds": "", "note": "", "git": r,
            })

    return {
        "projects": projects,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "fetched": fetch,
        "error": "; ".join(e for e in (reg_error, live_error) if e),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            try:
                self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b"index.html not found", "text/plain; charset=utf-8")
            return
        if parsed.path == "/api/projects":
            q = parse_qs(parsed.query)
            fetch = q.get("fetch", ["1"])[0] != "0"
            body = json.dumps(build_payload(fetch)).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def log_message(self, *args) -> None:  # keep the console quiet
        pass


def main() -> int:
    global PORT
    httpd = None
    for _ in range(15):
        try:
            httpd = ThreadingHTTPServer((HOST, PORT), Handler)
            break
        except OSError:
            PORT += 1
    if httpd is None:
        print("mission-control: could not bind a free port", file=sys.stderr)
        return 1

    url = f"http://{HOST}:{PORT}/"
    print(f"mission-control -> {url}   (Ctrl-C to stop)")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nmission-control: stopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
