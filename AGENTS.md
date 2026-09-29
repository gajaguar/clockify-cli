# AGENTS.md

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## What this is

`clockify-cli` is a Typer-based CLI for Clockify, built entirely on top of
[`clockify-unofficial-sdk`](https://github.com/gajaguar/clockify-sdk) — the
SDK owns HTTP, retries, pagination and typed models; the CLI owns profiles,
credentials, argument parsing, name-to-ID resolution, output formatting and
stable exit codes. Full spec: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Delivery phases: [`docs/ROADMAP.md`](docs/ROADMAP.md). Per-endpoint status:
[`docs/coverage.md`](docs/coverage.md).

## Agent instructions

`AGENTS.md` is the only agent instructions file. The repository MUST NOT
contain a `CLAUDE.md` or any other tool-specific copy; project rules go here.

## Commands

The agent MUST use these `Makefile` targets instead of invoking `ruff`,
`mypy`, `pyright`, `pylint`, `pytest`, `uv`, etc. directly, and MUST NOT add
a target without its `##` help line (`make help` lists them all).

```bash
make install          # mise toolchain, uv sync, pnpm tools, pre-commit hook
make check            # read-only CI gate (lint, format, types, spell, pylint, commits)
make fix              # safe auto-fixes (ruff format, ruff --fix, markdownlint --fix)
make fix-unsafe       # fix, including unsafe ruff fixes
make test             # pytest, 90% coverage floor, excludes -m live
make coverage         # pytest with an HTML coverage report
make build            # sdist and wheel into dist/
make commits-check    # commit range and branch name vs Conventional Commits/Branch
make openapi-fetch    # download Clockify's OpenAPI doc into .cache/
make coverage-report  # diff docs/coverage.md against the cached OpenAPI doc
```

- Most targets accept `FILES="..."` to scope to paths/globs, e.g.
  `make lint FILES="src/clockify_unofficial_cli/commands/auth.py"` or a
  single test: `make pytest FILES="tests/unit/commands/test_auth.py::test_login_ok"`.
- `check` (read-only, reports and exits non-zero, never writes) vs. `fix`
  (mutates in place) is a deliberate split — the CI gate only ever runs
  `check`.
- Live tests (`-m live`) hit the real Clockify API and need
  `CLOCKIFY_TEST_API_KEY`; `make test` excludes them by default.
- `make check` MUST pass before any commit; findings SHOULD be fixed with
  `make fix` before editing by hand.

## Architecture

Dependencies point downward only; commands never import `httpx`, services
never import Typer:

```text
main.py (root app, global options)
  -> commands/ (Typer sub-apps, one module per Clockify domain)
       -> services/ (product logic over the SDK: name resolution, multi-call workflows)
       -> runtime/ (AppContext, client factory, errors, exit codes)
            -> auth/ (credential store chain: env -> keyring -> file)
            -> config/ (platformdirs paths, TOML settings)
            -> output/ (Dataset -> Renderer: table/json/jsonl/csv/id)
       -> clockify SDK -> Clockify API
```

Request flow: the root Typer callback resolves global options
(flags > env > config file > defaults) into an `AppContext` on
`typer.Context.obj`. A command reads `get_app_context(ctx)`, calls a service
or the SDK directly, turns the result into a `Dataset`, and renders it via
`AppContext.render`. `AppContext.client()` builds the SDK client lazily so
offline commands (`--help`, `config ...`) never need a key. `handle_errors`
adapts `CliError`/SDK exceptions into a stderr message plus one of the
`ExitCode` values.

Design patterns worth knowing before adding code (details in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#design-patterns)): Command
(`commands/<domain>.py`, one `APP: Final = typer.Typer(...)` each, registered
in `main.create_app`), Facade (`services/`), lazy Factory
(`runtime/client_factory.py`), Application factory
(`main.create_app(services_factory)`), Strategy + Registry
(`output/formats.py` + `output/registry.py`, `auth/*_store.py`), Chain of
Responsibility (`CredentialStores.resolve`), Adapter (`runtime/errors.py`),
Parameter Object (`GlobalOptions`, `ResolvedOptions`, `Services`, `Dataset`,
`RenderTarget`).

Authentication has no OAuth2 available upstream (Clockify only exposes
header API keys) — see
[`docs/ARCHITECTURE.md#authentication`](docs/ARCHITECTURE.md#authentication)
before touching `auth/`.

## Commits and branches

Commit messages MUST follow
[Conventional Commits](https://www.conventionalcommits.org/); branch names
MUST follow [Conventional Branch](https://conventionalbranch.org/)
(`<type>/<description>`, e.g. `feat/add-login`). Documentation and
dependency work uses `chore/`, not `docs/`: a branch type is not a commit
type. A pre-commit hook and `make commits-check` enforce both — see
[`docs/conventions/commits-check.md`](docs/conventions/commits-check.md).

## Documentation

Documentation MUST be an OKF bundle of atomic notes under `docs/`: one
Markdown concept per file, with YAML frontmatter (`type`, `title`,
`description`). A new note MUST be added to its directory's `index.md` and
to [`docs/log.md`](docs/log.md). A note MUST cover exactly one concept, and
only when it explains something a reader can't already get from `make
help`, a linter's own message, or the configuration it comes from.

## Dependencies

A new tool MUST be added to the ecosystem manager that owns it and MUST
only go in `mise.toml` when it bootstraps an ecosystem or has none in this
repository — see
[`docs/toolchain/layering-rule.md`](docs/toolchain/layering-rule.md).

## Python

- The agent MUST NOT add docstrings to functions, methods, or classes; use a
  comment only where the _why_ is not obvious from the code. The
  `pylint-gajaguar` `gajaguar-no-docstrings` checker enforces this and fails
  `make check`/`make pylint` otherwise.
- pylint MUST enable the plugin with `enable = ["gajaguar"]` in
  `pyproject.toml`'s `[tool.pylint."messages control"]`, not with a list of
  rules, so a rule added by a `pylint-gajaguar` upgrade is never left off.
- `conventional-git` MUST be the latest PyPI release; `make
  conventional-git-latest` (part of `make check`) fails otherwise, and `make
  install` upgrades it.
- The agent MUST NOT add a `pyproject.toml` setting that equals the tool's
  default, and every `lint.per-file-ignores` entry MUST match a current
  violation — see
  [`docs/python/pyproject-defaults.md`](docs/python/pyproject-defaults.md).
- The agent MUST run `make check` and `make test` before committing Python
  changes, and SHOULD run `make fix` first for anything auto-fixable.

## clockify-cli project rules

These extend the sections above for this specific project.

- Commands MUST NOT call `httpx` or build Clockify URLs. A capability
  missing from `clockify-unofficial-sdk` MUST be added to the SDK first and
  pinned by tag in `[tool.uv.sources]` — see
  [`docs/ROADMAP.md`](docs/ROADMAP.md#cross-repo-workflow).
- Each command module MUST expose `APP: Final = typer.Typer(...)`, and every
  command MUST be decorated with `@APP.command(help=...)` then
  `@handle_errors`. Options MUST be declared inline with
  `Annotated[..., typer.Option(...)]` — Typer cannot resolve PEP 695 `type`
  aliases.
- Logic beyond a single SDK call MUST live in `services/`, not in a command.
- Commands MUST render data only through `AppContext.render` and write
  diagnostics only to stderr (`AppContext.notify`, `CliError`).
- New failure modes MUST reuse `ExitCode` (`runtime/exit_codes.py`); its
  values are a public contract and MUST NOT be renumbered.
- API keys MUST NOT be accepted as command-line arguments or printed
  outside `auth token`.
- MUST NOT silence `too-many-arguments`; apply the Parameter Object
  refactoring (frozen, `slots=True` dataclass) as the SDK does.
- Every endpoint change MUST update [`docs/coverage.md`](docs/coverage.md),
  and `make coverage-report` MUST pass.
- When adding a command, follow the checklist in
  [`docs/ARCHITECTURE.md#adding-a-command`](docs/ARCHITECTURE.md#adding-a-command):
  confirm SDK support, add/extend `commands/<domain>.py`, put multi-step
  logic in `services/`, add columns in `output/columns.py`, add
  `CliRunner` tests (success, JSON output, a failure exit code), flip the
  row in `docs/coverage.md`, then `make check && make test &&
make coverage-report`.
