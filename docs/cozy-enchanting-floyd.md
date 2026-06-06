# mission-control — board & masthead UX pass (cozy-enchanting-floyd)

## Context

The dashboard works but a review session surfaced a batch of UX issues: the TODO board eats vertical space, the self-backlog opens expanded and shoves the masthead around, priority isn't visually obvious, the loading terminal looks frozen during a slow Refresh, and there's no guard against duplicate sessions. This pass tightens the board into a priority-first, low-scroll surface, makes the masthead behave, and hardens launch/session handling.

**Working rule (from `CLAUDE.md`):** the running server rewrites `data/todos.json` on every board edit. So before editing files, **stop the server**, do all edits (code + tick the self-backlog), and only restart it at the end. This avoids the autosave race.

All UI work is in `src/index.html`; server/launch work in `src/serve.py` and `mission-control.cmd`.

---

## Tasks

### 1. Backlog widget collapsed by default
`selfboxOpen` restored from `localStorage["mc-selfbox"]` → always boot collapsed (`selfboxOpen = false`; don't read the key at startup).

### 2. Cap lanes to ~3 cards + scroll
`.lane-body`: `max-height` ≈ 3 cards (~360px) + `overflow-y: auto`. Order is already rank=priority, so the top 3 are visible; the rest scroll. Per-card note cap (`NOTE_CAP`/`autoGrow`) still applies.

### 3. Priority signal-bars — NEXT lane only
Small signal-bars SVG (no emoji) in each NEXT card header: rank0 = 3 bars lit, rank1 = 2, rank2 = 1, rank≥3 = 1 faint. Colour `--next`. Only when `lane === "next"`; omitted in NOW & LATER. Blocked cards excluded.

### 4. Edge hover-arrows to shift a card one lane
On card hover, ◄ at left edge / ► at right edge (absolute in `.tcard`). Click moves to the adjacent lane, appended at the **bottom**: left → toward NOW, right → toward LATER (`now0 next1 later2`). NOW hides left arrow; LATER hides right. Reuse move/rank logic from `onDrop`.

### 5. Block a 2nd session (launcher + browser)
- Launcher (`mission-control.cmd` both branches): probe `:8787` with `curl` first. If a mission-control server answers → print "already running … use your open tab", **wait for a keypress** (`pause` / `read -n1`), exit without opening a tab or auto-closing. Fresh start → existing countdown path.
- `serve.py` `probe_existing` path: stop auto-opening a browser when already running (no duplicate tab).
- Browser: `BroadcastChannel("mc")` — if another live tab answers, show a blocking overlay and don't run. Reuse `.killed-overlay` styling.

### 6. OS name bold + darker
`#os-name`: `font-weight: 600; color: var(--fg)`. `#os-detail` stays muted.

### 7. Double-click backlog → edit
`renderSelfBacklog`: `dblclick` on `.selfbox-body` → `selfboxEdit = true`, re-render, focus textarea.

### 8. Blocked / waiting mode
Pause-style SVG toggle in card header → `TODOS[name].blocked`. Blocked card: WAITING badge, muted, sinks to bottom of lane, excluded from signal-bars. Reason via existing notes. `laneItems` sort `(blocked?1:0)` then `rank`.

### 9. Sync notification persists +1.5s longer
After a successful Sync, keep the banner's success message ~1.5s longer via a `syncHold` flag that `renderSyncBanner` respects, then release + poll. Same for Kill & Close if trivial.

### 10. Terminal loading animation + surface the slowness
Refresh (`fetch=1`) runs `git fetch` on every repo (network × N) — that's the wait. While awaiting: braille spinner `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` + elapsed timer + "git fetch × N repos — network-bound". Real command log still replays on completion. Live per-command streaming deferred (SSE).

### 11. Backlog expands in place (no layout shift)
`.selfbox { position: relative }`, `.selfbox-body { position: absolute; top:100%; left:0; right:0; z-index; bg; border; shadow }` — opens within the middle column, never changes strip height, so left/right don't move.

### 12. Collapse the TODO board from its header line
Whole `.section-head` clickable to toggle `.board` (+ chevron). Hint text → exactly `drag n' drop · reorder priority · notes are autosaved:))`.

### 13. Move `server.log` into `logs/`
`serve.py`: `LOGFILE = ROOT / "logs" / "server.log"`; `mkdir(parents=True, exist_ok=True)` in `setup_output`. `.gitignore`: `server.log` → `logs/`. Update mentions in README/CLAUDE.

---

## Deferred / parked
- FTP-drift column (secure `.env`/config scanning pass later).
- Filters: lifecycle + handover.
- contact/creds, `wez-design` init, cross-machine renames.

## Self-backlog bookkeeping
Add tasks 1–13 to `TODOS["mission-control"].notes` as `- [ ]`, flip to `- [x]` as each lands (server stopped). User clears later.

## Verification
- `py_compile`; `logs/server.log` created, none at root.
- Launch, run again → "already running" + keypress, no 2nd tab; manual 2nd browser tab → blocked overlay.
- Lanes ~3 cards then scroll; NEXT signal-bars (top full), none NOW/LATER; edge ◄/► moves a card; pause-toggle → WAITING/sinks/no bars.
- Backlog starts collapsed; expand = popover, no left/right shift; dbl-click edits; `Windows 10` bold/dark.
- Click TODO BOARD line collapses board; hint `drag n' drop · reorder priority · notes are autosaved:))`.
- Sync message lingers +1.5s; Refresh shows spinner + elapsed + "git fetch × N".
- Restart reuses tab. Commit + push.

---

# Revision 2 (review follow-up)

A review of rev 1 produced these adjustments. Same working rule: stop the server, edit, restart last.

### 1. Edge arrows — one side only, outside the card
Show only the arrow on the side the cursor is on (left half → ◄, right half → ►), never both. Move them into the lane gutter just **outside** the card edge so they stop covering content: widen `.lane-body` side padding to ~18px and position `.tmove` at `left/right: -17px` (stays inside the lane's padding box, so the `overflow-y:auto` scroll area doesn't clip them). Side chosen via a `mousemove` handler toggling `.tcard.side-l/.side-r`; visibility gated on `.tcard:hover` (the arrow is a card descendant, so hovering it keeps the card "hovered"). Hidden arrows get `pointer-events:none`. NOW → only ►, LATER → only ◄.

### 3. Remove priority signal-bars
Delete the NEXT-lane signal-bars: the `.tbars` CSS, `signalBars()`, and the `bars` usage in `renderBoard`.

### 4. Blocked / waiting button bigger + clearer
Pause/resume glyph ~11→13px; `.tblock` default colour → `--muted`, rounded hover/active background tinted `--watch`, so it reads as a real toggle.

### 5. Backlog popover ~10 lines (view + edit)
Cap `.selfbox-body` to ~10 lines + scroll. The dbl-click/✎ edit textarea (`.sb-edit`) becomes a fixed ~10-line box (~200px) with its own scroll — stays 10 lines, doesn't auto-grow.

### 6. Status tally → up by the title
Move the bottom *In sync / Push / Pull / Attention* grid into a new `.mast-top` row, right of the title, as compact `dot + number` chips (`renderTally` rewritten). Labels hide under 600px so it always fits. Remove the bottom `.tally`.

### 7. Terminal: full Claude Code animation set
Replace the lone braille spinner with the signature look: a pulsing **star** glyph cycling `· ✢ ✳ ✶ ✻ ✽`, plus a **whimsical gerund verb** (full ~184-word list embedded) that rotates every ~2.5s, plus the elapsed timer and the `git fetch × N — network-bound` line.

### 8. Backlog add + sort + archive (`index.html` + `serve.py`)
- **"+" button** in the widget header → prepends a new `- [ ]` line at the top, enters edit mode, focuses with the cursor ready to type.
- **Checked items sink to the bottom** (render-time sort: open first, done last).
- **Archive button** → `POST /api/backlog/archive`; the server appends the `[x]` lines (each with `archived_at`) to **`data/backlog-archive.json`** (committed, syncs across machines), and the client strips them from the list. Auto-after-1-week is **deferred** (no per-item timestamps in the markdown format).

### 9. Terminal autoclose — full text on every line
Each countdown line reads the full `Autoclose in 3..`, `Autoclose in 2..`, `Autoclose in 1..` (currently only the first line has the words), still one line per second, then close.

### Scrollbars — themed for dark mode
Add themed scrollbars (`::-webkit-scrollbar*` + Firefox `scrollbar-color/width`) driven by theme vars, so the white default bars on the lanes / backlog / terminal turn dark in dark mode (and stay light-appropriate in Sun).

### Verify (rev 2)
Arrows show one-at-a-time in the gutter, never over text; no signal-bars; pause toggle bigger; backlog (both modes) caps at ~10 lines + scroll; tally sits by the title and survives a narrow window; terminal shows the star + rotating verbs; "+" adds at top, done items sink, Archive moves `[x]` into `data/backlog-archive.json`; autoclose lines all read "Autoclose in N.."; scrollbars are dark in dark mode.

---

# Revision 3 (polish follow-up)

- **Terminal animation confined + calmed.** The star sits in a fixed-width slot (`.spinner { display:inline-block; width:1.15em; text-align:center }`) so the verb no longer jumps as the glyph width changes; cadence slowed 120ms → 300ms; elapsed shows whole seconds. The verb now lives in its own `#tverb` span and **sweeps in left-to-right** on each change via a re-triggered `clip-path: inset(0 100% 0 0) → inset(0 0 0 0)` animation (`verbSweep`).
- **WeZimplify spinner words.** Claude's original ~184 verbs are kept in the file as `CLAUDE_VERBS` (unused); the active list is `WEZ_VERBS` — brand/security/dev words plus a little Danish (Zimplifying, Securing by design, Vibing, Hooking HubSpot, Lige om lidt, …).
- **Online-dot glow no longer clipped.** `.status-line` (an `.l2`, which is `overflow:hidden` for ellipsis) clipped the dot's box-shadow; `.sect-right .status-line { overflow: visible }` fixes the uneven halo.
- **Launcher OS banner.** `serve.py --osinfo` prints `System identified as <name> · <detail>`; `mission-control.cmd` calls it (after `chcp 65001` for the `·`) on both branches so the launch terminal shows e.g. `System identified as Windows 10 · 10.0.19045`.
