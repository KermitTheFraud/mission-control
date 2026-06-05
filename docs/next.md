# Next — mission-control

State: read-only dashboard working. `python serve.py` → http://127.0.0.1:8787 (serves index.html + `/api/projects`, merges projects.json with live git from `.tools/repo_check.py --json`). LAMP_toolbox archived to `Backups/`.

Update 2026-06-04 (work machine): mission-control now lives at `~/Projects/mission-control` inside the projects root. `repo_check.py` recreated INSIDE the repo at `.tools/repo_check.py` (version-controlled this time; serve.py points there and passes `--root <parent>`). Registry rebuilt: 16 cloned repos + 5 home-machine entries kept as "no scan". Launchers added (run.sh / run.command / run.bat). NOTE for home machine: on next pull, serve.py uses the in-repo `.tools/` - the old `../.tools/repo_check.py` is obsolete; align folder names (skattebob -> partner-ai.dk) or those registry rows show "no scan".

## Next
- ~~Launcher~~ DONE 2026-06-04: run.sh / run.command / run.bat in the repo, shell ones chmod +x.
- FTP-drift column — wire `repo_check.py --ftp` to a `/api/projects?ftp=1` toggle. (The recreated repo_check.py has no --ftp yet - port it from the home-machine version or rewrite.)
- Filters: lifecycle (live/watch/dormant/down) + handover, to isolate David's black-boxes fast.
- Surface nested repos (e.g. `WeZimplify/wez_crm`) — repo_check scans top-level only.
- Fill real contact + creds per project in projects.json.
- Decide fate of David black-boxes: Global Timber, Listbyg, new_agentbuilder, partner-revision.
- Optional: hard-delete `Backups/LAMP_toolbox` once confident (also on github.com/KermitTheFraud/LAMP_toolbox).

## Branch cleanup pass (bigger project, another day)

All 14 customer repos cloned to `~/Projects/` on this machine (2026-06-04). Local folder renames: `launis` -> `launis-ai.dk`, `skattebob` -> `partner-ai.dk` (GH repo names untouched). Old `Kongsvang` repo skipped as dead; active one is `kongsvang-agentbuilder`. Henning Mortensen repo not found, skipped.

Probe findings (blob-less bare clones, /tmp/wz-probe, 2026-06-04) - repos needing branch decisions:

- **DMR-ai.dk**: `mads-branch` ahead 71/behind 0, Mads committing daily. Fast-forward main to it, but coordinate with Mads first - it's his live branch.
- **skattebob / partner-ai.dk**: `skattebob_v2` ahead 22, `mads-branch` ahead 20 (both Mads, March). Check if v2 contains mads-branch, then merge v2 -> master, delete both.
- **Priess**: main = initial commit only. 4 unmerged branches: david-branch (28 ahead, newest), AndreasBranch1 (19), AndreasBranch (6), Peter-branch (2). david-branch is likely canon -> merge to main; decide keep/archive for the rest.
- **wallmann-ai.dk**: mads-branch + david-branch each ahead 2 / behind 18, old leftovers. Review the 2 commits each, likely delete.
- **Winther**: `mads` branch ahead 2 / behind 5 (Oct 2025), handed over. Likely delete branch.

Rest are single-branch, no action. Cross-cutting decisions parked: normalize master -> main (farmfood, kmrustfri, stennevad, skattebob, targarno, kongsvang-agentbuilder)? Push cleanup to WZ org or keep local-only until agreed with Mads?
