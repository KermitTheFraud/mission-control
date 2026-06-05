# mission-control

Local dashboard for every customer project in the projects root (`Github_repos/`).

- **What each project is** — static registry in [`data/projects.json`](data/projects.json) (summary, host, contact, creds, handover state).
- **Live git status** — merged in at serve time from [`src/repo_check.py`](src/repo_check.py) `--json` (ahead / behind / dirty / last commit).
- **TODO board** — a Now / Next / Later board with notes per customer, stored in [`data/todos.json`](data/todos.json) and synced across machines via git.

## Run

```bash
mission-control.cmd          # Windows (double-click or run it)
./mission-control.cmd        # macOS / Linux / Omarchy
# or directly:
python  src/serve.py         # Windows
python3 src/serve.py         # macOS / Linux / Omarchy
```

A browser opens at `http://127.0.0.1:8787`. No dependencies — Python 3.8+ and git on PATH. Open the page **through the server** (the localhost URL), not by double-clicking `index.html` — a `file://` page can't reach the API.

> The repo must live inside the projects root (`Github_repos/`): `serve.py` scans its parent directory for sibling git repos.

## Cross-machine TODOs

`serve.py` git-pulls this repo on startup (when the tree is clean), so starting it on another machine shows the latest board. Edits autosave locally; the **Sync** button commits + pushes `data/todos.json`. A banner appears when you have unsynced changes.

## Layout

```
mission-control/
├── mission-control.cmd   # one launcher, runs on Windows + Unix (sh/batch polyglot)
├── README.md
├── src/                  # serve.py, repo_check.py, index.html
├── data/                 # projects.json (registry), todos.json (the board)
└── docs/                 # next.md
```

## API

```
GET  /api/projects?fetch=0|1   registry + live git status
GET  /api/status               pid / port / uptime + this repo's git state
GET  /api/todos                the board
POST /api/todos                replace the board (body = full JSON object)
POST /api/sync                 commit + push data/todos.json
POST /api/shutdown             stop the server
POST /api/restart              re-exec (after pulling new code)
```

Start is intentionally *not* a button — a dead server can't serve one. Run the launcher, or autostart `serve.py` at login (Task Scheduler / launchd / `systemd --user`). The dashboard handles **Kill** and **Restart**.
