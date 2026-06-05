#!/usr/bin/env python3
"""
mission-control - local dashboard for every customer project.

Serves index.html plus a small JSON API:
    GET  /api/projects?fetch=0|1   registry (data/projects.json) + live git status
    GET  /api/status               server pid/port/uptime + this repo's git state
    GET  /api/todos                the TODO board (data/todos.json)
    POST /api/todos                replace the TODO board (body = full JSON object)
    POST /api/sync                 git add/commit/push data/todos.json
    POST /api/shutdown             stop the server
    POST /api/restart              re-exec the server (e.g. after a code pull)

Run:   python src/serve.py   /   python3 src/serve.py
Or the launcher in the repo root:  mission-control.cmd  (starts it detached)

Flags:
    --no-open    don't open a browser (used by Restart so it reuses your tab)
    --detached   redirect output to server.log (used when launched windowless)

Running the launcher when a server is already up just opens the browser - it
never starts a second one. On a fresh start it git-pulls the mission-control
repo (when the tree is clean) so switching machines shows the latest TODOs.

No third-party dependencies. Needs Python 3.8+ and git on PATH.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SELF = Path(__file__).resolve()
HERE = SELF.parent                 # mission-control/src
ROOT = HERE.parent                 # mission-control
SCAN_ROOT = ROOT.parent            # the projects root (Github_repos) - repos to scan
REPO_CHECK = HERE / "repo_check.py"
INDEX = HERE / "index.html"
REGISTRY = ROOT / "data" / "projects.json"
TODOS = ROOT / "data" / "todos.json"
LOGFILE = ROOT / "server.log"

HOST = "127.0.0.1"
PORT = 8787
START_TS = time.time()
START_ISO = datetime.now().isoformat(timespec="seconds")
DETACHED = False


def log(msg: str) -> None:
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)
    except Exception:
        pass


def setup_output(detached: bool) -> None:
    """When detached (or windowless via pythonw, where the std streams are None),
    send all output to server.log for debugging and an audit trail."""
    global DETACHED
    DETACHED = detached
    if detached or sys.stdout is None or sys.stderr is None:
        try:
            f = open(LOGFILE, "a", encoding="utf-8", buffering=1)
            sys.stdout = f
            sys.stderr = f
        except OSError:
            pass


# ---------------------------------------------------------------- git helpers

def git_root(*args: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run git inside the mission-control repo. Returns (code, stdout, stderr)."""
    try:
        p = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, "", str(e)


def repo_state() -> dict:
    """Sync state of the mission-control repo itself (drives the sync banner)."""
    st = {"branch": "", "dirty": 0, "ahead": 0, "behind": 0, "todos_dirty": False}
    code, branch, _ = git_root("rev-parse", "--abbrev-ref", "HEAD")
    if code == 0:
        st["branch"] = branch
    code, out, _ = git_root("status", "--porcelain")
    if code == 0:
        lines = [ln for ln in out.splitlines() if ln.strip()]
        st["dirty"] = len(lines)
        st["todos_dirty"] = any("data/todos.json" in ln for ln in lines)
    code, counts, _ = git_root("rev-list", "--left-right", "--count", "@{u}...HEAD")
    if code == 0 and counts:
        behind, _, ahead = counts.partition("\t")
        try:
            st["behind"], st["ahead"] = int(behind), int(ahead)
        except ValueError:
            pass
    return st


def pull_if_clean() -> str:
    code, out, _ = git_root("status", "--porcelain")
    if code != 0:
        return "git status failed - skipped pull"
    if out.strip():
        return "working tree not clean - skipped pull"
    code, out, err = git_root("pull", "--ff-only", timeout=60)
    if code == 0:
        return (out.splitlines() or ["pulled"])[-1]
    return f"pull failed: {err or out or 'unknown'}"


def do_sync() -> dict:
    git_root("add", "data/todos.json")
    code, _, _ = git_root("diff", "--cached", "--quiet")  # rc 1 == staged changes
    committed = False
    if code == 1:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        c, _, e = git_root("commit", "-m", f"todos: update {ts}")
        if c != 0:
            return {"ok": False, "message": f"commit failed: {e}"}
        committed = True
    c, out, err = git_root("push", timeout=60)
    if c != 0:
        return {"ok": False, "committed": committed, "message": f"push failed: {err or out}"}
    return {"ok": True, "committed": committed,
            "message": "committed + pushed" if committed else "already up to date"}


# ---------------------------------------------------------------- data helpers

def load_registry() -> tuple[list, str]:
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return (data.get("projects", []) if isinstance(data, dict) else data), ""
    except (OSError, json.JSONDecodeError) as e:
        return [], f"could not read projects.json: {e}"


def load_todos() -> dict:
    try:
        data = json.loads(TODOS.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_todos(data: dict) -> None:
    TODOS.parent.mkdir(parents=True, exist_ok=True)
    tmp = TODOS.with_name(TODOS.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, TODOS)


def run_repo_check(fetch: bool) -> tuple[list, str, list]:
    wrapper = "$ python src/repo_check.py --json --root <projects>" + ("" if fetch else " --no-fetch")
    if not REPO_CHECK.exists():
        return [], f"repo_check.py not found at {REPO_CHECK}", [wrapper]
    cmd = [sys.executable, str(REPO_CHECK), "--json", "--log", "--root", str(SCAN_ROOT)]
    if not fetch:
        cmd.append("--no-fetch")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        return [], "repo_check.py timed out", [wrapper]
    except OSError as e:
        return [], f"could not run repo_check.py: {e}", [wrapper]
    log_lines = [wrapper] + [ln for ln in (proc.stderr or "").splitlines() if ln.strip()]
    try:
        return json.loads(proc.stdout), "", log_lines
    except json.JSONDecodeError:
        tail = (proc.stderr or proc.stdout or "no output").strip().splitlines()
        return [], "repo_check.py did not return JSON: " + (tail[-1] if tail else "?"), log_lines


def build_payload(fetch: bool) -> dict:
    registry, reg_error = load_registry()
    live, live_error, log_lines = run_repo_check(fetch)
    live_by_name = {r.get("name"): r for r in live}

    projects, seen = [], set()
    for p in registry:
        seen.add(p.get("name"))
        projects.append({**p, "git": live_by_name.get(p.get("name"))})
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
        "log": log_lines,
        "error": "; ".join(e for e in (reg_error, live_error) if e),
    }


def status_payload() -> dict:
    return {
        "app": "mission-control",
        "pid": os.getpid(), "host": HOST, "port": PORT,
        "started_at": START_ISO, "uptime_seconds": int(time.time() - START_TS),
        "repo": repo_state(),
    }


# ---------------------------------------------------------------- http handler

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            try:
                self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b"index.html not found", "text/plain; charset=utf-8")
        elif path == "/api/projects":
            q = parse_qs(urlparse(self.path).query)
            fetch = q.get("fetch", ["1"])[0] != "0"
            self._json(200, build_payload(fetch))
        elif path == "/api/status":
            self._json(200, status_payload())
        elif path == "/api/todos":
            self._json(200, load_todos())
        elif path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/todos":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("expected a JSON object")
                save_todos(data)
                self._json(200, {"ok": True})
            except (ValueError, OSError) as e:
                self._json(400, {"ok": False, "error": str(e)})
        elif path == "/api/sync":
            self._json(200, do_sync())
        elif path == "/api/shutdown":
            self._json(200, {"ok": True, "message": "shutting down"})
            threading.Thread(target=self._delayed_shutdown, daemon=True).start()
        elif path == "/api/restart":
            self._json(200, {"ok": True, "message": "restarting"})
            threading.Thread(target=self._delayed_restart, daemon=True).start()
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def _delayed_shutdown(self) -> None:
        time.sleep(0.3)
        log("shutdown requested")
        self.server.shutdown()

    def _delayed_restart(self) -> None:
        time.sleep(0.3)
        log("restart requested")
        # execv replaces the process; the listening socket is close-on-exec, so
        # the new one can rebind. --no-open reuses the browser tab you already
        # have; keep --detached so a windowless instance stays windowless.
        args = [sys.executable, str(SELF), "--no-open"]
        if DETACHED:
            args.append("--detached")
        os.execv(sys.executable, args)

    def log_message(self, *args) -> None:  # keep access logging quiet
        pass


def probe_existing() -> str:
    """If a mission-control server already owns the port, return its URL."""
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/api/status", timeout=1.5) as r:
            data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("app") == "mission-control":
                return f"http://{HOST}:{PORT}/"
    except Exception:
        pass
    return ""


def main() -> int:
    global PORT
    argv = sys.argv[1:]
    no_open = "--no-open" in argv
    setup_output("--detached" in argv)

    existing = probe_existing()
    if existing:
        log(f"already running -> {existing} (opening browser)" if not no_open
            else f"already running -> {existing}")
        if not no_open:
            webbrowser.open(existing)
        return 0

    log(f"startup: {pull_if_clean()}")

    httpd = None
    for _ in range(15):
        try:
            httpd = ThreadingHTTPServer((HOST, PORT), Handler)
            break
        except OSError:
            PORT += 1
    if httpd is None:
        log("ERROR: could not bind a free port")
        return 1

    url = f"http://{HOST}:{PORT}/"
    log(f"serving {url} (pid {os.getpid()})")
    if not no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("stopped (Ctrl-C)")
    except Exception as e:
        log(f"ERROR: {e}")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
