---
type: playbook
title: Installing through the Claude Code marketplace
description: Add a marketplace, install a plugin from it, and reload plugins — the in-session flow.
tags: [agents, claude-code]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Installing through the Claude Code marketplace

Use the `/plugin` slash commands inside a Claude Code session to add
a marketplace, install a plugin from it, and apply the change without
restarting.[^claude-discover-plugins]

## Two commands

```text
/plugin marketplace add <owner>/<repo>[#ref]
/plugin install <plugin>@<marketplace>
```

`<ref>` defaults to the marketplace's default branch. The marketplace
name comes from the marketplace's `.claude-plugin/marketplace.json`;
the plugin name comes from its `.claude-plugin/plugin.json`. Both
names are listed in [`plugin-identity.md`](plugin-identity.md).

## One-command shortcut

To add a marketplace and install a plugin from it in a single step,
pass `--marketplace`:

```text
/plugin install <plugin>@<owner>/<repo>[#ref] --marketplace
```

The install scope defaults to **user** — the plugin is available in
every project for the current user. Use `--scope project` to scope the
install to this checkout only. See
[`claude-code-install-scopes.md`](claude-code-install-scopes.md) for
what that means on disk.

## Reload

A change to the marketplace, a plugin's manifest, or its skills
requires a reload before Claude Code picks it up:

```text
/reload-plugins
```

Run this once after the install, and again whenever you update the
plugin.

[^claude-discover-plugins]: Discover and install Claude Code plugins
