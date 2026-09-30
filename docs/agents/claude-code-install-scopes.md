---
type: reference
title: Claude Code install scopes
description: user, project, and local scopes — which settings file each writes to, the precedence order, and when each is the right choice.
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

# Claude Code install scopes

Every install — by `/plugin install` or `claude plugin install` —
writes to a settings file under one of three scopes.[^claude-discover-plugins]
Higher scopes win when the same key is set in more than
one.[^claude-loading]

| Scope    | Settings file                                       | Shared with   |
| :------- | :-------------------------------------------------- | :------------ |
| `user`   | `~/.claude/settings.json`                           | Nothing       |
| `project`| `.claude/settings.json` in the repo root            | Collaborators |
| `local`  | `.claude/settings.local.json` (gitignored)          | Nothing       |

## Which scope to pick

* **`user`** — the default. The install follows the user across every
  project they open. Use it for skills you want everywhere.
* **`project`** — the install is committed in `.claude/settings.json`
  and shared with collaborators on the same repo. Use it when the
  project itself depends on the plugin. Expect collaborators to
  approve the change.
* **`local`** — the install lives in a gitignored file and follows
  the working tree only. Use it for personal overrides that must not
  pollute `git status`.

## Precedence

When the same setting is set in more than one scope, `local` wins
over `project`, which wins over `user`. A `project`-scope install is
overridden by a `local`-scope override in the same working
tree.[^claude-loading]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-loading]: How Claude Code loads plugins
