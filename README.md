# mission-control

Read-only dashboard over every customer project in `Github_repos/`.

- **What each project is** — static registry in [`projects.json`](projects.json) (summary, host, contact, creds, handover state).
- **Live git status** — merged in at serve time from [`../.tools/repo_check.py`](../.tools/repo_check.py) `--json` (ahead / behind / dirty / last commit). FTP drift can be layered on later.

## Run

```bash
python serve.py      # Windows
python3 serve.py     # macOS / Linux / Omarchy
```

A browser opens at `http://127.0.0.1:8787`. Ctrl-C to stop. No dependencies — just Python 3.8+ and git on PATH. Works the same on all three machines.

> Must live inside `Github_repos/` next to `.tools/` — `serve.py` calls `../.tools/repo_check.py`. Open the page **through the server** (the localhost URL), not by double-clicking `index.html` (a `file://` page can't reach `/api/projects`).

First paint uses local git refs (instant); **Refresh** re-runs the scan and fetches remotes.

## How it fits together

```
browser ──GET /──────────────▶ index.html        (the view)
        ──GET /api/projects──▶ serve.py
                                  ├─ reads projects.json        (registry)
                                  └─ runs repo_check.py --json  (live git)
                                  └─ merges by repo name ──────▶ JSON
```

Add or edit a project = edit `projects.json`. The `name` must match the repo's folder name so live git status can attach to it.
