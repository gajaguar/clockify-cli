---
type: playbook
title: Updating and uninstalling Claude Code plugins
description: Auto-update is off for third-party marketplaces — update by hand, then reload; uninstall by removing the plugin and the marketplace.
tags: [agents, claude-code]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
  - id: claude-loading
    resource: https://code.claude.com/docs/en/plugins/loading
    title: How Claude Code loads plugins
    author: team:anthropic
---

# Updating and uninstalling Claude Code plugins

Third-party marketplaces do not auto-update by default — they leave the
user to opt in.[^claude-loading]

## Update by hand

In a Claude Code session:

```text
/marketplace update                # refresh the marketplace's index
/plugin update <plugin>@<marketplace>   # pull the latest version
/reload-plugins                    # apply
```

In a script or CI job, the same three commands have a CLI form —
`claude plugin marketplace update`, `claude plugin update`, and the
reload happens automatically.[^claude-discover-plugins]

## Disable without uninstall

Use `/plugin disable <plugin>@<marketplace>` (or `claude plugin
disable`) to keep the install on disk but skip loading. Useful for
debugging when a skill fires unexpectedly.

## Uninstall

In a Claude Code session:

```text
/plugin uninstall <plugin>@<marketplace>
/marketplace remove <marketplace>
```

A `plugin uninstall` leaves the marketplace entry behind. Run
`/marketplace remove` to drop it too.[^claude-discover-plugins]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-loading]: How Claude Code loads plugins
