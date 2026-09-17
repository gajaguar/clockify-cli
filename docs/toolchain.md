# Toolchain

- **mise** — pins the high-level toolchain (`mise.toml`): Node, pnpm,
  pre-commit, and — on language branches — the language runtime itself
  (e.g. Python, uv). Per-language package managers keep doing their own job
  (uv for Python, pnpm for Node).
- **markdownlint-cli2** + **cspell** (pnpm, dev-only) — Markdown lint and
  spell check. Configuration is canonical on `main`; a language branch only
  appends its own dictionary words and ignore paths.
- **checkmake** — lints the `Makefile` itself (`make makefile-lint`);
  `checkmake.ini` disables the `minphony` rule's `all`/`clean` expectations,
  which don't apply to this Makefile's install/check/fix/test shape.
- **pre-commit** — git hook running the universal hooks from `main`
  (whitespace/EOF/YAML/TOML checks, markdownlint, cspell) plus whatever a
  language branch appends to `.pre-commit-config.yaml`.
