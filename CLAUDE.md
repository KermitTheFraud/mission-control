# mission-control

Local dashboard for every project in the projects root (`github-repos/`). Runs on
the same three machines (Windows, macOS, Omarchy). No third-party deps — Python
3.8+ and git on PATH.

## Run

- `mc-windows.cmd` (Windows) / `mc-unix.command` (macOS/Linux double-click, or
  `./mc-unix.command` in a terminal) — start `src/serve.py --detached` and open
  `http://127.0.0.1:8787`. Re-running just reopens the tab; it never starts a second server.
- Always open the page **through the server**, never `file://` (a file page can't reach the API).

## Files

| Path | What |
|------|------|
| `src/serve.py` | HTTP server + JSON API; merges the registry with live git status; git-pulls on startup; Sync/Kill/Restart endpoints. |
| `src/repo_check.py` | Scans the projects root for git repos, emits one JSON object per repo (ahead/behind/dirty/last commit). |
| `src/index.html` | The whole UI (vanilla JS, no build step). |
| `data/projects.json` | Static registry of customer projects (the human facts). |
| `data/internal.json` | Registry of internal WeZimplify repos (which live in `../wez-internal/`); shown under the Internal tab. |
| `data/todos.json` | The Now/Next/Later board — synced across machines via git. |

Projects are split into two groups — **customer** (top-level repos in the projects root) and
**internal** (repos under the sibling `../wez-internal/` folder) — shown on Customers / Internal
tabs. `serve.py` scans each separately and tags every project with a `group`; a loose repo not in
its registry stays inside its own group, so internal repos never leak into the customer list.

## Data flow / API map

The browser is dumb; `serve.py` does the work. Endpoints (all under `http://127.0.0.1:8787`):

| Method + path | Handler in `serve.py` | What it returns / does |
|---------------|-----------------------|------------------------|
| `GET /` | `do_GET` → reads `index.html` | The whole UI. |
| `GET /api/projects?fetch=0\|1` | `build_payload` → `merge_group` ×2 → `run_repo_check` | Registry (`projects.json` + `internal.json`) merged with live git from `repo_check.py`. `fetch=0` skips network `git fetch`. |
| `GET /api/status` | `status_payload` → `repo_state` + `detect_os` | Server pid/port/uptime, this repo's git state, OS, git email. |
| `GET /api/todos` | `load_todos` | The Now/Next/Later board (`data/todos.json`). |
| `POST /api/todos` | `save_todos` | Replaces the board (body = full JSON object). Writes LF. |
| `POST /api/sync` | `do_sync` | `git add/commit/push data/todos.json`. |
| `POST /api/backlog/archive` | `archive_backlog` | Moves finished backlog lines to `data/backlog-archive.json`. |
| `POST /api/shutdown` / `POST /api/restart` | threaded | Stop / re-exec the server (restart reuses your tab). |

The one path worth holding in your head:
**browser → `GET /api/projects` → `serve.py:build_payload()` → `merge_group()` runs `repo_check.py` (live git) and merges it over the static `data/*.json` registries → JSON back to the page.** A repo found by the scan but absent from the registry shows up as a loose "review" card in its own group.

## Self-backlog convention

**The `mission-control` entry in [`data/todos.json`](data/todos.json) is this dashboard's
own dev backlog**, surfaced as a collapsible **checklist in the masthead** (middle column),
not as a board lane card. Its `notes` are one item per line using markdown checkboxes —
`- [ ]` open, `- [x]` done — stored as a plain string so they still sync across machines and
stay editable (the ✎ toggle in the widget reveals a raw textarea).

Any agent (Claude Code or otherwise) working on mission-control should:

1. **Read the checklist first** — the `- [ ]` items are the task list. Proactively propose a
   plan for the open ones.
2. **Plan + get approval**, then implement.
3. **Tick items off.** As you implement an item, change its line in `data/todos.json` from
   `- [ ]` to `- [x]` — the checkboxes are read-only in the UI, only an agent crosses them off.
   Completed items render greyed + struck.
4. **The user clears them.** Don't delete items yourself; once everything is `- [x]` and the
   user is satisfied, they remove the completed lines. The widget is collapse-only / not removable.

Mind the autosave race: the running server rewrites `data/todos.json` on every board edit, so
only edit that file when the board is idle (or stop the server first).

## Gotchas

- The repo is LF everywhere (`.gitattributes` `* text=auto eol=lf`) — the `.cmd` polyglot's
  sh side breaks on CRLF. `save_todos` writes with `newline="\n"` for the same reason.
- `data/todos.json` is written by the server; don't hand-edit it while the server is running
  (the next autosave will overwrite). Edit through the board, or stop the server first.
- `serve.py` derives the projects root dynamically (`ROOT.parent`) — it does **not** hardcode
  the folder name, so it works regardless of what the root folder is called on each machine.
