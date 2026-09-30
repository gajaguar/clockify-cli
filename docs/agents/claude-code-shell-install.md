---
type: playbook
title: Installing from a script or CI
description: The `claude plugin` CLI mirrors the /plugin slash commands and is what to call from a script or CI job.
tags: [agents, claude-code, ci]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
  - id: claude-cli-reference
    resource: https://code.claude.com/docs/en/plugins/cli-reference
    title: Claude Code plugin CLI reference
    author: team:anthropic
---

# Installing from a script or CI

The `claude plugin` subcommand mirrors the `/plugin` slash
commands[^claude-discover-plugins] and is what a script or CI job
calls. It is non-interactive when called without a TTY and accepts
`--yes` to skip every confirmation prompt.[^claude-cli-reference]

## Commands

```bash
claude plugin marketplace add <owner>/<repo>[#ref] --scope user
claude plugin install <plugin>@<marketplace> --scope user --yes
claude plugin list
```

## Scopes

`--scope` accepts `user`, `project`, or `local`. The default scope
depends on whether the command runs inside a project directory; pass
`--scope` explicitly in scripts so the install does not depend on the
working directory. See
[`claude-code-install-scopes.md`](claude-code-install-scopes.md) for
what each scope writes to.

## CI recipe

A CI job that needs the plugin only for the duration of the run
should install at `user` scope, run the gate, and uninstall at the
end:

```bash
claude plugin marketplace add <repo> --scope user --yes
claude plugin install <plugin>@<marketplace> --scope user --yes
make check
claude plugin marketplace remove <name> --scope user --yes
```

The marketplace add/remove pair is needed even when uninstalling,
because a marketplace entry persists after a plugin uninstall.[^claude-cli-reference]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-cli-reference]: Claude Code plugin CLI reference
