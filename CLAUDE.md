# mission-control

Local dashboard for every project in the projects root (`github-repos/`). Runs on
the same three machines (Windows, macOS, Omarchy). No third-party deps — Python
3.8+ and git on PATH.

## Run

- `mission-control.cmd` (Windows) / `mission-control.command` (Mac/Linux double-click)
  / `./mission-control.cmd` (terminal) — all start `src/serve.py --detached` and open
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

## Self-backlog convention

**The `mission-control` entry in [`data/todos.json`](data/todos.json) is this dashboard's
own dev backlog.** Its `notes` are a numbered list of improvements to make to
mission-control itself (kept here so they sync across machines and stay editable from the
board UI — that card is styled distinctly from customer cards to make this obvious).

When working on mission-control:

1. **Read** the `mission-control` card's `notes` first — treat them as the task list.
2. **Plan** the items, get the user's approval, then implement.
3. **Ask before clearing.** After the noted items are implemented and the user has eyeballed
   them, ask the user to confirm, then blank the card's `notes` so it's fresh for the next round.
   Never clear notes that haven't been implemented and confirmed.

## Gotchas

- The repo is LF everywhere (`.gitattributes` `* text=auto eol=lf`) — the `.cmd` polyglot's
  sh side breaks on CRLF. `save_todos` writes with `newline="\n"` for the same reason.
- `data/todos.json` is written by the server; don't hand-edit it while the server is running
  (the next autosave will overwrite). Edit through the board, or stop the server first.
- `serve.py` derives the projects root dynamically (`ROOT.parent`) — it does **not** hardcode
  the folder name, so it works regardless of what the root folder is called on each machine.
