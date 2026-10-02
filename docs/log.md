# Directory Update Log

## 2026-10-01

* **Update**: The SDK now comes from PyPI instead of a `uv` git source, so
  `README.md`, `AGENTS.md`, `ROADMAP.md` and `ARCHITECTURE.md` describe
  raising the SDK floor instead of bumping a tag.

## 2026-09-30

* **Update**: Removed the `generated` field from `agents/plugin-identity.md`,
  added its Repository row, and synced the shared `agents/` notes with the
  seed.
* **Update**: Changed the `type` of `ARCHITECTURE.md` to `reference` and of
  `ROADMAP.md` and `toolchain/releasing.md` to `playbook`, which are in the
  note type vocabulary.
* **Update**: Dropped a mention of how the project was generated from
  `ROADMAP.md`.

## 2026-09-29

* **Addition**: Added `docs/agents/` with `plugin-identity.md` filled in for
  this project (marketplace `clockify-cli-skills`, plugin `clockify-cli`,
  skills `clockify-time-tracking` and `clockify-cli`), the
  shared agent notes, and the
  per-project index in `docs/agents/index.md`. No MCP server for this
  project.
* **Addition**: Added `toolchain/claude-plugin.md`, which describes the Claude
  Code plugin and its two skills.
* **Update**: Added the `skills-ref` row to `toolchain/layering-rule.md` and
  the manifest version to the steps in `toolchain/releasing.md`.
* **Restructure**: Brought `docs/` to an OKF bundle: added frontmatter to
  `ARCHITECTURE.md`, `ROADMAP.md` and `coverage.md`, added `index.md`, and
  added the conventions, toolchain and python notes.
* **Removal**: Deleted the flat `conventions.md` and `toolchain.md`, which
  only described how the repository was generated.
* **Addition**: Added `python/typer-parameter-objects.md`, which explains
  `options_from` and when a command uses it.
* **Update**: Marked Phase 1 as done in `ROADMAP.md` and flipped the Phase 1
  rows in `coverage.md`.
* **Addition**: Added `toolchain/releasing.md`, which describes the tag-driven
  PyPI publish workflow.
