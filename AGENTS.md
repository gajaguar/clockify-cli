# AGENTS.md

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Agent instructions

- `AGENTS.md` is the only agent instructions file; put project rules here. The
  repository MUST NOT contain a `CLAUDE.md` or any other tool-specific copy,
  because a second copy drifts from this one.

## Command surface

- Run the `Makefile` targets (`make check`, `make fix`, `make test`, ...)
  instead of the underlying tools, so the agent and CI use the same options.
  `make help` lists them.
- Give every new target a `##` help line; `make help` prints it.
- `make test` skips the `live` tests, which call the real Clockify API; run
  them only with `CLOCKIFY_TEST_API_KEY` set.

## Gate

- `make check` and `make test` MUST pass before any commit.
- Run `make fix` first for findings it can repair, then edit by hand.

## Commits and branches

- Write commit messages as
  [Conventional Commits](https://www.conventionalcommits.org/) and branch
  names as [Conventional Branch](https://conventionalbranch.org/)
  (`<type>/<description>`, e.g. `feat/add-login`). A pre-commit hook and
  `make commits-check` enforce both; see
  [`docs/conventions/commits-check.md`](docs/conventions/commits-check.md).
- Name a documentation or dependency branch `chore/...`: a branch type is not
  a commit type, and `docs/` is not one.

## Pull requests

Once a pull request is open, the agent MUST:

1. Wait for CI; while it fails, fix the cause, push to the same branch and
   wait again until it passes.
2. Squash-merge a pull request with exactly one commit and use a regular merge
   commit otherwise (`gh pr view --json commits` gives the count).
3. Delete the branch on the remote and locally.
4. Switch back to the base branch, pull it and run `git fetch --prune`.

## Documentation

- Write documentation as an OKF bundle of atomic notes under `docs/`: one
  Markdown concept per file, with YAML frontmatter (`type`, `title`,
  `description`).
- Add a new note to its directory's `index.md` and, by file name, to
  [`docs/log.md`](docs/log.md); `make docs-lint` fails on a missing field or a
  broken link.
- Write a note only when it explains something a reader cannot already get
  from `make help`, a linter's own message, or the configuration it comes
  from.

## Dependencies

- Add a new tool to the ecosystem manager that owns it; use `mise.toml` only
  for a tool that bootstraps an ecosystem or has no manager in this
  repository. See
  [`docs/toolchain/layering-rule.md`](docs/toolchain/layering-rule.md).

## Python

- Write no docstrings on functions, methods or classes; add a comment only
  where the *why* is not obvious from the code. `pylint-gajaguar`'s
  `gajaguar-no-docstrings` fails `make check` on any docstring.
- Enable the plugin with `enable = ["gajaguar"]` in `pyproject.toml`'s
  `[tool.pylint."messages control"]`, not with a list of rules, so a rule
  added by a `pylint-gajaguar` upgrade runs without a config change.
- Keep `pyproject.toml` to settings that differ from the tool's default, and
  keep a `lint.per-file-ignores` entry only while it matches a current
  violation; see
  [`docs/python/pyproject-defaults.md`](docs/python/pyproject-defaults.md).

## Architecture

- Read [Layering](docs/ARCHITECTURE.md#layering) before adding code:
  dependencies point downward only, from `commands/` through `services/` and
  `runtime/` to the SDK.
- Read [Authentication](docs/ARCHITECTURE.md#authentication) before changing
  `auth/`: Clockify offers header API keys only, no OAuth2.
- Add a command by following
  [Adding a command](docs/ARCHITECTURE.md#adding-a-command), which ends with
  `make check`, `make test` and `make coverage-report`.

## Clockify rules

- Reach Clockify only through `clockify-unofficial-sdk`, never with `httpx`
  or a hand-built URL, so retries, pagination and models stay in one place.
  Add a missing capability to the SDK first and raise the SDK floor in
  `pyproject.toml` once it is released; see
  [Cross-repo workflow](docs/ROADMAP.md#cross-repo-workflow).
- Expose each command module as `APP: Final = typer.Typer(...)`, decorate
  every command with `@APP.command(help=...)` then `@handle_errors`, and
  declare options inline as `Annotated[..., typer.Option(...)]`, because
  Typer cannot resolve PEP 695 `type` aliases.
- Put logic beyond a single SDK call in `services/`.
- Render data only through `AppContext.render`, and write diagnostics to
  stderr through `AppContext.notify` or `CliError`, so `-o json` output
  stays parseable.
- Report a new failure with an existing `ExitCode`
  (`runtime/exit_codes.py`). Its values are a public contract: add a value,
  never renumber one.
- Read API keys from the credential stores only. A key MUST NOT be accepted
  as a command-line argument or printed outside `auth token`, because shell
  history and logs would keep it.
- Replace a long argument list with a Parameter Object (a frozen,
  `slots=True` dataclass), as the SDK does, instead of silencing
  `too-many-arguments`; see
  [Typer parameter objects](docs/python/typer-parameter-objects.md).
- Update [`docs/coverage.md`](docs/coverage.md) with every endpoint change;
  `make coverage-report` checks it against the OpenAPI document.
