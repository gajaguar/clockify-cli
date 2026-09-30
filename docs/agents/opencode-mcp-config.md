---
type: reference
title: opencode MCP configuration
description: The mcp key (type, command, enabled, environment), config path precedence, and `opencode mcp list`.
tags: [agents, opencode, mcp]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: opencode-mcp
    resource: https://opencode.ai/docs/mcp-servers/
    title: opencode MCP servers
    author: team:sst-opencode
  - id: opencode-config
    resource: https://opencode.ai/docs/config/
    title: opencode config
    author: team:sst-opencode
---

# opencode MCP configuration

opencode reads MCP server definitions from its own config file under
an `mcp` key.[^opencode-mcp]

## The `mcp` block

```json
{
  "mcp": {
    "<name>": {
      "type": "local",
      "command": ["<executable>", "<arg>", "..."],
      "enabled": true,
      "environment": { "<KEY>": "<value>" }
    }
  }
}
```

| Key           | Purpose                                                            |
| :------------ | :----------------------------------------------------------------- |
| `type`        | `"local"` for a process; the only value today                      |
| `command`     | Argument array: executable first, then each argument               |
| `enabled`     | `true` (default) to load; `false` to keep on disk but skip         |
| `environment` | Extra environment variables to inject into the server's process    |

## Path precedence

opencode loads config files in this order; later files override earlier
ones on conflict.[^opencode-config]

1. Built-in defaults
2. `~/.config/opencode/config.json`
3. `opencode.json` in the project root
4. `.opencode/config.json` in the project root

A local MCP server for one project lives in
`.opencode/config.json` (or `opencode.json` at the project root). A
server shared across projects lives in the global config.

## Listing servers

```bash
opencode mcp list
```

Prints every configured server, its type, its command, and whether it
is enabled. The same set powers the agent's available tools at
runtime.[^opencode-mcp]

[^opencode-mcp]: opencode MCP servers
[^opencode-config]: opencode config
