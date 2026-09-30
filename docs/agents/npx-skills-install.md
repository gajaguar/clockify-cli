---
type: playbook
title: Installing skills with `npx skills`
description: npx skills add copies a repo's skills/ into one or more agent paths; flags for scope, list-only, and global install.
tags: [agents, npx-skills]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: vercel-skills
    resource: https://github.com/vercel-labs/skills
    title: vercel-labs/skills (the `npx skills` CLI)
    author: team:vercel-labs
  - id: skills-sh
    resource: https://skills.sh
    title: skills.sh
    author: team:vercel-labs
---

# Installing skills with `npx skills`

`npx skills` ([vercel-labs/skills](https://github.com/vercel-labs/skills))
copies a repository's `skills/` directory into the path each agent
expects, no plugin hooks or MCP. It is the right channel when the
agent is not Claude Code or the project does not need auto-update.[^vercel-skills]

## Install one or more agents at once

```bash
npx skills add <owner>/<repo> -a claude-code -a opencode -y
```

`-a` accepts `claude-code`, `opencode`, and others. `-y` accepts the
prompts.

## Flags

| Flag       | Effect                                                              |
| :--------- | :------------------------------------------------------------------ |
| `-a AGENT` | Add an agent to the install; pass twice for two agents              |
| `-g`       | Global install (user scope) instead of the current directory        |
| `-s`       | Symlink instead of copy                                             |
| `-y`       | Accept every prompt                                                 |
| `--list`   | Print the skills the install would write; do not write              |
| `--copy`   | Copy the skills into the working directory instead of installing    |

## Where `npx skills` writes

`npx skills add` chooses a per-agent path automatically. The full
list comes from the CLI's own help; the most common paths are:

| Agent         | Project path          | Global path                  |
| :------------ | :-------------------- | :--------------------------- |
| `claude-code` | `.claude/skills/`     | `~/.claude/skills/`          |
| `opencode`    | `.opencode/skills/`   | `~/.config/opencode/skills/` |

Run `npx skills add --list <owner>/<repo>` first when the destination
is unclear — it prints the resolved targets without writing.[^skills-sh]

[^vercel-skills]: vercel-labs/skills (the `npx skills` CLI)
[^skills-sh]: skills.sh
