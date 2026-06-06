# Refactor idea: split `index.html` into ES modules

Status: **idea / not started.** Written up to think on before doing it. Nothing here
is committed to yet — enhance, cut, or reorder before pulling the trigger.

## Why

`src/index.html` is ~1100 lines: markup + `<style>` + all the JS in one file. It works
fine at runtime. The problem is **editability** — especially for an AI agent (and honestly
for a human too):

- A single 1100-line file means big reads, fuzzy "where does X live", and risky edits
  (a unique match string is hard to find; a bad edit can land in the wrong place).
- Smaller, single-responsibility files = smaller reads, obvious location, safe edits.
- No runtime upside, no design change. This is purely a maintainability move.

**Hard constraint: keep the no-build-step, no-dependency property.** The whole charm of
mission-control is "clone, double-click, it runs with just Python + git." Any refactor that
introduces npm / a bundler / a `dist/` is off the table. ES modules let us split *without* a build.

## What "ES modules" means (the mechanism this relies on)

ES modules = the browser's native way to split JS across files. You mark a script with
`type="module"` and then `import` / `export` between files — the browser fetches them itself.
No bundler, no build, no tooling.

```html
<!-- index.html -->
<script type="module" src="js/app.js"></script>
```
```js
// js/api.js
export async function getProjects(fetch = true) {
  const r = await fetch(`/api/projects?fetch=${fetch ? 1 : 0}`);
  return r.json();
}
```
```js
// js/app.js
import { getProjects } from "./api.js";
const data = await getProjects();
```

Two things to know:
- Modules **only load over http(s)**, not `file://`. We already require opening through the
  server (never `file://`), so this changes nothing for us — but it's why the "always open via
  the server" rule in CLAUDE.md matters even more after the split.
- Each module is its own scope (no accidental globals), and imports are explicit, so it's
  obvious what depends on what.

## Proposed structure

Keep everything under `src/`. One possible split (refine before building):

```
src/
  index.html        markup shell only — no <style>, no inline <script>
  css/
    style.css       everything currently in <style>
  js/
    app.js          entry point: wires modules together, kicks off first render
    api.js          fetch wrappers, one per endpoint (see API map in CLAUDE.md)
    state.js        in-memory model + a tiny pub/sub so render reacts to changes
    render.js       DOM building (or split per area: board, projects, masthead)
```

Rough mapping from today's single file:
- `<style>` block → `css/style.css`
- all `fetch("/api/...")` calls → `js/api.js`
- the data the page holds + "re-render when it changes" → `js/state.js`
- functions that build/patch DOM → `js/render.js` (split further if it gets big)

## Open questions / things to decide first

- **How granular?** One `render.js`, or per-section files (`render.board.js`,
  `render.projects.js`, `render.masthead.js`)? Depends on how big each turns out.
- **State approach.** Plain module-level object + manual re-render is simplest and dependency-free.
  Worth a tiny pub/sub, or keep it dumb? (No framework either way — that'd break the no-deps rule.)
- **CSS too, or just JS?** Pulling `<style>` out is cheap and high-value; could be a separate
  first step before touching JS.
- **Optional: `// @ts-check` + JSDoc.** After the split, adding `// @ts-check` at the top of each
  module gives editor/`tsc --noEmit` typechecking **with no build and no shipped TS**. Browser still
  runs plain JS. Could be a follow-up once modules exist.
- **Migration order.** Suggested: (1) extract CSS, (2) extract `api.js`, (3) extract `state.js`,
  (4) extract `render.js`, verifying the page still works after each step. Small commits, easy to revert.

## Definition of done

- Page looks and behaves **1:1** with today (design unchanged).
- Still starts with `mc-windows.cmd` / `mc-unix.command`, no new install step, no `node_modules`.
- No file over ~300 lines.
- CLAUDE.md "Files" table updated to list the new modules.
