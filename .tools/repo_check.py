#!/usr/bin/env python3
"""
repo_check - live git status for every repo in the projects root.

Scans the top-level directories of --root (default: the folder containing
mission-control, i.e. two levels up from this file) and reports one JSON
object per git repo. Output schema is what mission-control's index.html
expects under each project's "git" key:

    name, status, branch, upstream, ahead, behind, dirty_count,
    last_commit {sha, subject, age},
    ahead_commits / behind_commits [{sha, subject}]

status is one of: IN SYNC, PUSH, PULL, DIVERGED, DIRTY, NO UPSTREAM, ERROR.

Usage:
    repo_check.py --json [--no-fetch] [--root PATH]

Exit code 1 means "some repos need attention" - not a failure.
No third-party dependencies. Needs Python 3.8+ and git on PATH.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
GIT_TIMEOUT = 30  # seconds per git command (fetch can be slow)


def git(repo: Path, *args: str, timeout: int = GIT_TIMEOUT) -> tuple[int, str]:
    """Run a git command in repo. Returns (exit_code, stdout)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip()
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, f"__error__: {e}"


def humanize_age(epoch: int) -> str:
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(epoch, timezone.utc)
    s = int(delta.total_seconds())
    if s < 3600:
        return f"{max(s // 60, 1)}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    days = s // 86400
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def commit_list(repo: Path, range_spec: str, limit: int = 5) -> list[dict]:
    code, out = git(repo, "log", "--format=%h\t%s", f"-{limit}", range_spec)
    if code != 0 or not out:
        return []
    rows = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\t")
        rows.append({"sha": sha, "subject": subject})
    return rows


def check_repo(repo: Path, fetch: bool) -> dict:
    r: dict = {
        "name": repo.name, "status": "ERROR", "branch": "", "upstream": "",
        "ahead": 0, "behind": 0, "dirty_count": 0, "last_commit": None,
        "ahead_commits": [], "behind_commits": [],
    }

    code, branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if code != 0:
        return r
    r["branch"] = branch

    code, last = git(repo, "log", "-1", "--format=%h\t%ct\t%s")
    if code == 0 and last:
        sha, _, rest = last.partition("\t")
        epoch, _, subject = rest.partition("\t")
        r["last_commit"] = {"sha": sha, "subject": subject,
                            "age": humanize_age(int(epoch))}

    if fetch:
        git(repo, "fetch", "--quiet")

    code, dirty = git(repo, "status", "--porcelain")
    r["dirty_count"] = len(dirty.splitlines()) if code == 0 and dirty else 0

    code, upstream = git(repo, "rev-parse", "--abbrev-ref",
                         "--symbolic-full-name", "@{upstream}")
    if code != 0:
        r["status"] = "DIRTY" if r["dirty_count"] else "NO UPSTREAM"
        return r
    r["upstream"] = upstream

    code, counts = git(repo, "rev-list", "--left-right", "--count",
                       f"{upstream}...HEAD")
    if code == 0 and counts:
        behind, _, ahead = counts.partition("\t")
        r["behind"], r["ahead"] = int(behind), int(ahead)

    if r["ahead"]:
        r["ahead_commits"] = commit_list(repo, f"{upstream}..HEAD")
    if r["behind"]:
        r["behind_commits"] = commit_list(repo, f"HEAD..{upstream}")

    if r["dirty_count"]:
        r["status"] = "DIRTY"
    elif r["ahead"] and r["behind"]:
        r["status"] = "DIVERGED"
    elif r["ahead"]:
        r["status"] = "PUSH"
    elif r["behind"]:
        r["status"] = "PULL"
    else:
        r["status"] = "IN SYNC"
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON (the only mode)")
    ap.add_argument("--no-fetch", action="store_true", help="skip git fetch (faster, offline)")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help=f"projects root to scan (default: {DEFAULT_ROOT})")
    args = ap.parse_args()

    root = args.root.resolve()
    repos = sorted(
        (d for d in root.iterdir() if d.is_dir() and (d / ".git").exists()),
        key=lambda d: d.name.lower(),
    )
    results = [check_repo(d, fetch=not args.no_fetch) for d in repos]

    print(json.dumps(results, indent=None if args.json else 2))
    return 1 if any(r["status"] != "IN SYNC" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
