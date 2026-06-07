#!/usr/bin/env python3
"""
mission-control - local dashboard for every customer project.

Serves index.html plus a small JSON API:
    GET  /api/projects?fetch=0|1   registry (data/projects.json) + live git status
    GET  /api/status               server pid/port/uptime + this repo's git state
    GET  /api/todos                the TODO board (data/todos.json)
    POST /api/todos                replace the TODO board (body = full JSON object)
    POST /api/sync                 git add/commit/push data/todos.json
    POST /api/backlog/archive      move finished backlog items to data/backlog-archive.json
    POST /api/shutdown             stop the server
    POST /api/restart              re-exec the server (e.g. after a code pull)

Run:   python src/serve.py   /   python3 src/serve.py
Or a launcher in the repo root:  mc-windows.cmd / mc-unix.command  (starts it detached)

Flags:
    --no-open    don't open a browser (used by Restart so it reuses your tab)
    --detached   redirect output to logs/server.log (used when launched windowless)

Running the launcher when a server is already up just opens the browser - it
never starts a second one. On a fresh start it git-pulls the mission-control
repo (when the tree is clean) so switching machines shows the latest TODOs.

No third-party dependencies. Needs Python 3.8+ and git on PATH.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
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
SCAN_ROOT = ROOT.parent            # the projects root (github-repos) - customer repos to scan
REPO_CHECK = HERE / "repo_check.py"
INDEX = HERE / "index.html"
REGISTRY = ROOT / "data" / "projects.json"      # customer projects
INTERNAL = ROOT / "data" / "internal.json"      # internal WeZimplify product repos
INTERNAL_DIR = SCAN_ROOT / "wez-internal"       # subfolder the internal repos live in
TODOS = ROOT / "data" / "todos.json"
ARCHIVE = ROOT / "data" / "backlog-archive.json"   # retired self-backlog items
LOGFILE = ROOT / "logs" / "server.log"

HOST = "127.0.0.1"
PORT = 8787
START_TS = time.time()
START_ISO = datetime.now().isoformat(timespec="seconds")
DETACHED = False
# CREATE_NO_WINDOW: stop child console apps (git) from popping a console window
# when we run windowless under pythonw. 0 (no-op) on non-Windows.
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def log(msg: str) -> None:
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)
    except Exception:
        pass


def setup_output(detached: bool) -> None:
    """When detached (or windowless via pythonw, where the std streams are None),
    send all output to logs/server.log for debugging and an audit trail."""
    global DETACHED
    DETACHED = detached
    if detached or sys.stdout is None or sys.stderr is None:
        try:
            LOGFILE.parent.mkdir(parents=True, exist_ok=True)
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
            errors="replace", timeout=timeout, creationflags=NO_WINDOW,
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

def load_registry(path: Path) -> tuple[list, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return (data.get("projects", []) if isinstance(data, dict) else data), ""
    except FileNotFoundError:
        return [], ""  # an optional registry (e.g. internal.json) simply absent
    except (OSError, json.JSONDecodeError) as e:
        return [], f"could not read {path.name}: {e}"


def load_todos() -> dict:
    try:
        data = json.loads(TODOS.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_todos(data: dict) -> None:
    TODOS.parent.mkdir(parents=True, exist_ok=True)
    tmp = TODOS.with_name(TODOS.name + ".tmp")
    # newline="\n" so Windows doesn't write CRLF (the repo is LF via .gitattributes)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, TODOS)


def archive_backlog(items: list) -> dict:
    """Append finished self-backlog lines to data/backlog-archive.json (a committed,
    cross-machine record) so the live backlog widget can drop them."""
    arr = []
    try:
        existing = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        if isinstance(existing, list):
            arr = existing
    except (OSError, json.JSONDecodeError):
        arr = []
    ts = datetime.now().isoformat(timespec="seconds")
    for text in items:
        arr.append({"text": text, "archived_at": ts})
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARCHIVE.with_name(ARCHIVE.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:   # LF, like save_todos
        f.write(json.dumps(arr, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, ARCHIVE)
    return {"ok": True, "archived": len(items), "total": len(arr)}


def run_repo_check(fetch: bool, root: Path) -> tuple[list, str, list]:
    wrapper = f"$ python src/repo_check.py --json --root {root.name}" + ("" if fetch else " --no-fetch")
    if not REPO_CHECK.exists():
        return [], f"repo_check.py not found at {REPO_CHECK}", [wrapper]
    cmd = [sys.executable, str(REPO_CHECK), "--json", "--log", "--root", str(root)]
    if not fetch:
        cmd.append("--no-fetch")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120,
                              creationflags=NO_WINDOW)
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


def merge_group(registry_path: Path, scan_root: Path, group: str,
                fetch: bool) -> tuple[list, list, list]:
    """Build the project list for one group (customer / internal): registry
    entries with live git merged in, plus any scanned repo not yet in the
    registry as a loose 'review' card. Returns (projects, errors, log_lines).
    A loose repo stays inside its own group, so internal repos never leak into
    the customer list (or vice versa)."""
    registry, reg_error = load_registry(registry_path)
    errors = [reg_error] if reg_error else []
    live, log_lines = [], []
    if scan_root.exists():
        live, live_error, log_lines = run_repo_check(fetch, scan_root)
        if live_error:
            errors.append(live_error)
    live_by_name = {r.get("name"): r for r in live}

    projects, seen = [], set()
    for p in registry:
        seen.add(p.get("name"))
        projects.append({**p, "group": group, "git": live_by_name.get(p.get("name"))})
    for name, r in live_by_name.items():
        if name not in seen:
            projects.append({
                "name": name, "title": name, "lifecycle": "", "handover": "review",
                "summary": "Tracked by repo_check but not in the registry yet.",
                "tech": [], "url": "", "host": "", "repo": name,
                "contact": "", "creds": "", "note": "", "group": group, "git": r,
            })
    return projects, errors, log_lines


def build_payload(fetch: bool) -> dict:
    cust, cust_err, cust_log = merge_group(REGISTRY, SCAN_ROOT, "customer", fetch)
    intern, int_err, int_log = merge_group(INTERNAL, INTERNAL_DIR, "internal", fetch)

    return {
        "projects": cust + intern,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "fetched": fetch,
        "log": cust_log + int_log,
        "error": "; ".join(e for e in (cust_err + int_err) if e),
    }


_OS_CACHE = None


def detect_os() -> dict:
    """Short OS name + exact version, for the three machines this runs on
    (Windows / macOS / Omarchy). Cached - the OS doesn't change at runtime."""
    global _OS_CACHE
    if _OS_CACHE is not None:
        return _OS_CACHE

    sysname = platform.system()
    if sysname == "Windows":
        release, version, *_ = platform.win32_ver()
        info = {"name": f"Windows {release}".strip(), "detail": version}
    elif sysname == "Darwin":
        ver = platform.mac_ver()[0]              # e.g. "26.3.1"
        # The marketing codename isn't exposed by Python or sw_vers - map it
        # from the major version. Update this each fall when Apple ships a name.
        names = {26: "Tahoe", 15: "Sequoia", 14: "Sonoma",
                 13: "Ventura", 12: "Monterey", 11: "Big Sur"}
        try:
            codename = names.get(int(ver.split(".")[0]))
        except (ValueError, IndexError):
            codename = None
        info = {"name": f"macOS {codename}" if codename else "macOS", "detail": ver}
    elif sysname == "Linux":
        info = None
        omarchy = shutil.which("omarchy")
        if omarchy:
            try:
                p = subprocess.run([omarchy, "--version"], capture_output=True,
                                   text=True, timeout=5, creationflags=NO_WINDOW)
                v = (p.stdout or p.stderr).strip()
                if v:
                    info = {"name": "Omarchy", "detail": v.split()[-1]}
            except (OSError, subprocess.SubprocessError):
                pass
        if info is None:
            try:
                for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
                    if line.startswith("PRETTY_NAME="):
                        info = {"name": line.split("=", 1)[1].strip().strip('"'), "detail": ""}
                        break
            except OSError:
                pass
        if info is None:
            info = {"name": "Linux", "detail": platform.release()}
    else:
        info = {"name": sysname, "detail": platform.release()}

    _OS_CACHE = info
    return info


def git_email() -> str:
    code, out, _ = git_root("config", "user.email")
    return out if code == 0 else ""


def status_payload() -> dict:
    return {
        "app": "mission-control",
        "pid": os.getpid(), "host": HOST, "port": PORT,
        "started_at": START_ISO, "uptime_seconds": int(time.time() - START_TS),
        "git_email": git_email(),
        "os": detect_os(),
        "repo": repo_state(),
    }


# ---------------------------------------------------------------- http handler

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, OSError):
            pass  # client closed the tab mid-response - ignore

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
        elif path == "/api/backlog/archive":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
                items = data.get("items") if isinstance(data, dict) else None
                if not isinstance(items, list):
                    raise ValueError("expected an items array")
                self._json(200, archive_backlog([str(x) for x in items]))
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


def preflight() -> str:
    """Verify the two things this tool assumes are on the machine: Python 3.8+
    (we're clearly running *some* Python, but bail loudly on an ancient one) and
    git on PATH. Returns an error string if something's missing, else ""."""
    if sys.version_info < (3, 8):
        have = ".".join(map(str, sys.version_info[:3]))
        return (f"Python 3.8+ required, but this is {have}. "
                "Install a newer Python from https://www.python.org/downloads/")
    if shutil.which("git") is None:
        return ("git not found on PATH. Install it from https://git-scm.com/downloads "
                "and reopen your terminal.")
    return ""


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

    problem = preflight()
    if problem:
        log(f"ERROR: {problem}")
        return 1

    existing = probe_existing()
    if existing:
        # Already up: never open a second tab - the launcher tells the user to
        # use the tab they already have, and the in-page BroadcastChannel guards
        # against duplicate browser tabs.
        log(f"already running -> {existing} (use your open tab)")
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
    if "--osinfo" in sys.argv:
        # Bare OS string for the launcher banner, e.g. "macOS Tahoe · 26.3.1".
        # The launchers add their own "SYSTEM" label + styling around it.
        _os = detect_os()
        _line = _os["name"] + (" · " + _os["detail"] if _os.get("detail") else "")
        print(_line)
        sys.exit(0)
    sys.exit(main())
