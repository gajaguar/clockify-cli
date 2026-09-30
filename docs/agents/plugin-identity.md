---
type: reference
title: Plugin identity
description: The marketplace, plugin, and skill names for this project, plus the prerequisites and copy-ready install commands.
resource: https://github.com/gajaguar/clockify-cli
tags: [agents]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Plugin identity

This project ships as a Claude Code plugin and an Agent Skills
directory.[^claude-discover-plugins] It does not ship an MCP server.
The marketplace, plugin, and skill names below match this repository's
own `.claude-plugin/` and `skills/` directories.

## Names

| Asset         | Name                                                    |
| :------------ | :------------------------------------------------------ |
| Marketplace   | `clockify-cli-skills`                                   |
| Plugin        | `clockify-cli`                                          |

## Skills

| Skill                    | Trigger phrasing                                                                                                                                                              |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `clockify-time-tracking` | "start a timer", "stop tracking", "log 2h on project X", "what am I tracking", "my time entries today", fix a Clockify entry                                                  |
| `clockify-cli`           | "clockify login", "switch workspace", "create a project", "list tags", "add a client", how to use the clockify command                                                        |

## Prerequisites

- Install the `clockify-unofficial-cli` Python package
  (`pipx install clockify-unofficial-cli` or
  `uv tool install clockify-unofficial-cli`).
- Run `clockify auth login` before the skills will work — they
  delegate to a Clockify API key the CLI reads from its own config
  file.

## Install

Claude Code:

```text
/plugin marketplace add gajaguar/clockify-cli
/plugin install clockify-cli@clockify-cli-skills
/reload-plugins
```

Any other Agent Skills-compatible agent:

```bash
npx skills add gajaguar/clockify-cli
```

opencode:

```bash
npx skills add gajaguar/clockify-cli -a opencode -y
```

## Examples

See [`install-channels.md`](install-channels.md) for what each channel
delivers, and the rest of `docs/agents/` for scopes, management, and
the opencode configuration notes.

[^claude-discover-plugins]: Discover and install Claude Code plugins
