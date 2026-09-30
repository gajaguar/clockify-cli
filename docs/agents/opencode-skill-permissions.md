---
type: reference
title: opencode skill permissions
description: permission.skill (allow / deny / ask by name pattern) and the per-agent skill: false switch.
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

# opencode skill permissions

Two configuration knobs gate which skills opencode is willing to load.
Both live in opencode's own config file.[^opencode-skills]

## `permission.skill`

The `permission.skill` key accepts a list of patterns, each one of:

* `"<skill-name>` — allow loading of the named skill.
* `"ask <skill-name>`":
  prompt the user before loading.
* `"deny <skill-name>`:
  refuse to load the named skill.

A pattern matches by skill name (the `name` in `SKILL.md`); glob
patterns are not supported. Default is to allow every discovered
skill.

## Per-agent `skill: false`

Each agent block in the config may set `skill: false` to disable
skill loading for that agent entirely. Useful when an agent should
never pick up a skill (for example a documentation-only agent).

[^opencode-skills]: opencode Skills
