# Next — mission-control

State: read-only dashboard working. `python serve.py` → http://127.0.0.1:8787 (serves index.html + `/api/projects`, merges projects.json with live git from `.tools/repo_check.py --json`). LAMP_toolbox archived to `Backups/`.

## Next
- **Launcher** — one-click script to start the server + open the browser (no typing the command):
  - `run.command` (macOS) / `run.sh` (Linux/Omarchy) / `run.bat` (Windows), each just runs `serve.py` (which already opens the browser).
  - `chmod +x` the shell ones so they're double-clickable.
- FTP-drift column — wire `repo_check.py --ftp` to a `/api/projects?ftp=1` toggle.
- Filters: lifecycle (live/watch/dormant/down) + handover, to isolate David's black-boxes fast.
- Surface nested repos (e.g. `WeZimplify/wez_crm`) — repo_check scans top-level only.
- Fill real contact + creds per project in projects.json.
- Decide fate of David black-boxes: Global Timber, Listbyg, new_agentbuilder, partner-revision.
- Optional: hard-delete `Backups/LAMP_toolbox` once confident (also on github.com/KermitTheFraud/LAMP_toolbox).
