---
type: reference
title: Invoking a Claude Code skill
description: The /<plugin>:<skill> slash form, automatic triggering by description, and how to verify a skill is installed.
tags: [agents, claude-code, skills]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-skills
    resource: https://code.claude.com/docs/en/skills
    title: Claude Code skills
    author: team:anthropic
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Invoking a Claude Code skill

A skill from an installed plugin is invoked two ways.[^claude-skills][^claude-discover-plugins]

## Explicit invocation

The slash form `<plugin>:<skill>` invokes the skill directly:

```text
/<plugin>:<skill>
```

The skill name (`<skill>`) is the directory under the plugin's
`skills/`. The plugin name (`<plugin>`) is the one in its
`.claude-plugin/plugin.json`. Both are listed in
[`plugin-identity.md`](plugin-identity.md).

## Automatic triggering

Claude Code reads every installed skill's `description` and may
trigger one without an explicit slash command when the user's request
matches the description's phrasing. The description is the only field
the agent sees before triggering — a skill that wants to be triggered
must put its user phrasing in `description`.[^claude-skills]

## Verifying the install

Inside a Claude Code session:

```text
/plugin list                # installed plugins
/<plugin>:                  # tab completion lists the skills'
```

Outside Claude Code, the install lives under the settings file for the
scope chosen at install time — see
[`claude-code-install-scopes.md`](claude-code-install-scopes.md).

[^claude-skills]: Claude Code skills
[^claude-discover-plugins]: Discover and install Claude Code plugins
