---
type: reference
title: opencode skill discovery
description: The paths opencode scans for skills, the worktree walk-up rule, the skill tool, and name validation.
tags: [agents, opencode]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: opencode-skills
    resource: https://opencode.ai/docs/skills/
    title: opencode Skills
    author: team:sst-opencode
---

# opencode skill discovery

opencode discovers skills from a fixed set of paths and exposes them
through the `skill` tool.[^opencode-skills]

## Project paths

opencode scans, in priority order:

1. `.opencode/skill/` in the working directory
2. `.claude/skills/` in the working directory
3. `.agents/skills/` in the working directory

## Worktree walk-up

The scan walks the directory tree up to the worktree root (typically
the git worktree's top), not the filesystem root. A skill placed in a
project's top-level `.opencode/skill/` is visible from any subdirectory
of the same worktree.

## Global paths

When no project skill matches, opencode falls back to:

* `~/.config/opencode/skill/`
* `~/.claude/skills/`
* `~/.agents/skills/`

The `skill` tool can list every discovered skill and load any one of
them into context on demand.

## Name validation

opencode validates each `SKILL.md`'s `name` field: it must match the
folder name, must be lowercase, and may only contain letters, digits,
and dashes. A skill whose `name` does not match its folder is
silently skipped.

[^opencode-skills]: opencode Skills
