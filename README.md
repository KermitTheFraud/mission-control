# mission-control

Local dashboard for every project in the projects root (`github-repos/`) — **customer** projects plus WeZimplify's own **internal** repos, on two tabs.

- **What each project is** — static registry in [`data/projects.json`](data/projects.json) (customers) and [`data/internal.json`](data/internal.json) (internal): summary, host, contact, creds, handover state.
- **Live git status** — merged in at serve time from [`src/repo_check.py`](src/repo_check.py) `--json` (ahead / behind / dirty / last commit).
- **Customers / Internal tabs** — customers are the top-level repos in the projects root; internal repos live in the sibling `wez-internal/` folder. Drop a git repo into `wez-internal/` and it appears under Internal automatically (add it to `internal.json` for a proper title).
- **TODO board** — a Now / Next / Later board with notes per project, stored in [`data/todos.json`](data/todos.json) and synced across machines via git.

## Run

```bash
mc-windows.cmd               # Windows (double-click or run it)
mc-unix.command              # macOS / Linux (double-click in Finder)
./mc-unix.command            # macOS / Linux / Omarchy (terminal)
# or directly:
python  src/serve.py         # Windows
python3 src/serve.py         # macOS / Linux / Omarchy
```

`mc-unix.command` is the double-clickable Mac/Linux launcher (`mc-windows.cmd` is the Windows one). For a one-click Dock icon, drag it onto the Dock (documents side) and set a custom icon via **Finder → Get Info → paste an image onto the icon**. The Terminal window it opens can auto-close via **Terminal → Settings → Profiles → Shell → "When the shell exits: Close if the shell exited cleanly"**.

A browser opens at `http://127.0.0.1:8787`. No dependencies — Python 3.8+ and git on PATH. Open the page **through the server** (the localhost URL), not by double-clicking `index.html` — a `file://` page can't reach the API.

> The repo must live inside the projects root (`github-repos/`): `serve.py` scans its parent directory for sibling git repos (customers) plus the `wez-internal/` subfolder (internal). The root can be named anything — `serve.py` locates it dynamically — but it's standardised to `github-repos` across the three machines.

## Cross-machine TODOs

`serve.py` git-pulls this repo on startup (when the tree is clean), so starting it on another machine shows the latest board. Edits autosave locally; the **Sync** button commits + pushes `data/todos.json`. A banner appears when you have unsynced changes.

## Layout

```
mission-control/
├── mc-windows.cmd            # Windows launcher (batch)
├── mc-unix.command           # macOS / Linux launcher (sh, double-clickable)
├── CLAUDE.md                 # how to work on this repo + the self-backlog convention
├── README.md
├── src/                      # serve.py, repo_check.py, index.html
├── data/                     # projects.json + internal.json (registries), todos.json (board)
└── docs/                     # next.md
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
