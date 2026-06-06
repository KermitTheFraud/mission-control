# Next — mission-control

State: working. `python3 src/serve.py` → http://127.0.0.1:8787 (serves index.html + JSON API; merges `data/projects.json` + `data/internal.json` with live git from `src/repo_check.py`). Editable TODO board, synced via git. LAMP_toolbox archived to `BACKUPS/`.

Update 2026-06-04 (work machine): mission-control now lives at `~/Projects/mission-control` inside the projects root. `repo_check.py` recreated INSIDE the repo at `.tools/repo_check.py` (version-controlled this time; serve.py points there and passes `--root <parent>`). Registry rebuilt: 16 cloned repos + 5 home-machine entries kept as "no scan". Launchers added (run.sh / run.command / run.bat). NOTE for home machine: on next pull, serve.py uses the in-repo `.tools/` - the old `../.tools/repo_check.py` is obsolete; align folder names (skattebob -> partner-ai.dk) or those registry rows show "no scan".

Update 2026-06-06 (mac): Cross-platform + internal-repos pass.
- Launchers consolidated to one sh/batch polyglot `mission-control.cmd` + a double-click `mission-control.command` (Mac/Linux). The 06-04 `run.sh/.command/.bat` and `.tools/repo_check.py` references are obsolete — `repo_check.py` now lives at `src/repo_check.py`. (Later renamed + split into `mc-windows.cmd` (batch) + `mc-unix.command` (sh).)
- Added `CLAUDE.md`: project orientation + the **self-backlog convention** (the `mission-control` card's notes in `data/todos.json` are this dashboard's own backlog — read, implement, then clear after sign-off).
- UI: notes textareas auto-grow to fit content; Refresh shows a plain-language explainer; the mission-control "self" card is colour-coded (magenta).
- **Internal repos**: `WeZimplify/` subfolder renamed → `wez-internal/` and scanned as a second group. `data/internal.json` registers wez_crm / wez-website / wez-docs / wez-design. UI now has **Customers | Internal** tabs (`serve.py` tags each project `group: customer|internal`; loose/unregistered repos stay in their own group, no cross-leak).
- Root project folder standardised to **`github-repos`** (was `Github_repos` on Windows, `Projects` on Omarchy). `serve.py` locates the root dynamically, so this is for human/doc consistency, not a code requirement.

## Next
- ~~Launcher~~ DONE: `mission-control.cmd` (sh/batch polyglot) + `mission-control.command` (Mac/Linux double-click). Superseded the 06-04 run.sh/.command/.bat.
- ~~Surface nested repos~~ DONE 2026-06-06: internal repos under `wez-internal/` scanned as a second group, shown under the Internal tab (`data/internal.json`).
- **Cross-machine sync of the renames** — do on Omarchy + Windows (this mac is done):
  - Omarchy: `mv ~/Projects ~/github-repos` then `mv ~/github-repos/WeZimplify ~/github-repos/wez-internal`
  - Windows: rename `github_repos` → `github-repos` and `WeZimplify` → `wez-internal`
  - Then regenerate `tools/projects.json` absolute paths on that machine (they bake in the root path).
- `wez-design`: `git init` + add a WeZimplify remote + push, so it leaves "no scan" in the Internal tab.
- FTP-drift column — wire `repo_check.py --ftp` to a `/api/projects?ftp=1` toggle (no `--ftp` in `src/repo_check.py` yet).
- Filters: lifecycle (live/watch/dormant/down) + handover, to isolate David's black-boxes fast.
- Fill real contact + creds per project in projects.json.
- Decide fate of David black-boxes: Global Timber, Listbyg, new_agentbuilder, partner-revision.
- Optional: hard-delete `BACKUPS/LAMP_toolbox` once confident (also on github.com/KermitTheFraud/LAMP_toolbox).

## Branch cleanup pass (bigger project, another day)

All 14 customer repos cloned to `~/Projects/` on this machine (2026-06-04). Local folder renames: `launis` -> `launis-ai.dk`, `skattebob` -> `partner-ai.dk` (GH repo names untouched). Old `Kongsvang` repo skipped as dead; active one is `kongsvang-agentbuilder`. Henning Mortensen repo not found, skipped.

Probe findings (blob-less bare clones, /tmp/wz-probe, 2026-06-04) - repos needing branch decisions:

- **DMR-ai.dk**: `mads-branch` ahead 71/behind 0, Mads committing daily. Fast-forward main to it, but coordinate with Mads first - it's his live branch.
- **skattebob / partner-ai.dk**: `skattebob_v2` ahead 22, `mads-branch` ahead 20 (both Mads, March). Check if v2 contains mads-branch, then merge v2 -> master, delete both.
- **Priess**: main = initial commit only. 4 unmerged branches: david-branch (28 ahead, newest), AndreasBranch1 (19), AndreasBranch (6), Peter-branch (2). david-branch is likely canon -> merge to main; decide keep/archive for the rest.
- **wallmann-ai.dk**: mads-branch + david-branch each ahead 2 / behind 18, old leftovers. Review the 2 commits each, likely delete.
- **Winther**: `mads` branch ahead 2 / behind 5 (Oct 2025), handed over. Likely delete branch.

Rest are single-branch, no action. Cross-cutting decisions parked: normalize master -> main (farmfood, kmrustfri, stennevad, skattebob, targarno, kongsvang-agentbuilder)? Push cleanup to WZ org or keep local-only until agreed with Mads?
