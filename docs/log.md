# Directory Update Log

## 2026-09-29 (Agents)

* **Addition**: Added `docs/agents/` with `plugin-identity.md` filled in for
  this project (marketplace `clockify-cli-skills`, plugin `clockify-cli`,
  skills `clockify-time-tracking` and `clockify-cli`), the
  byte-identical shared notes that ship with the template, and the
  per-project index in `docs/agents/index.md`. No MCP server for this
  project.

## 2026-09-29 (Plugin)

* **Addition**: Added `toolchain/claude-plugin.md`, which describes the Claude
  Code plugin and its two skills.
* **Update**: Added the `skills-ref` row to `toolchain/layering-rule.md` and
  the manifest version to the steps in `toolchain/releasing.md`.

## 2026-09-29

* **Restructure**: Brought `docs/` to an OKF bundle: added frontmatter to
  `ARCHITECTURE.md`, `ROADMAP.md` and `coverage.md`, added `index.md`, and
  added the conventions, toolchain and python notes.
* **Removal**: Deleted the flat `conventions.md` and `toolchain.md`, which
  only described how the repository was generated.

## 2026-09-29 (Phase 1)

* **Addition**: Added `python/typer-parameter-objects.md`, which explains
  `options_from` and when a command uses it.
* **Update**: Marked Phase 1 as done in `ROADMAP.md` and flipped the Phase 1
  rows in `coverage.md`.

## 2026-09-29 (Release)

* **Addition**: Added `toolchain/releasing.md`, which describes the tag-driven
  PyPI publish workflow.
