---
type: reference
title: Agent Skills format
description: SKILL.md, its required and recommended fields, progressive disclosure, and the references/ subdirectory.
tags: [agents, skills]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: agentskills-spec
    resource: https://agentskills.io/specification
    title: Agent Skills specification
    author: team:agentskills
---

# Agent Skills format

An Agent Skill is a directory that contains a `SKILL.md` file with YAML
frontmatter. A skill's `description` is what Claude Code and other
agents scan to decide when to trigger the skill automatically.[^agentskills-spec]

| Field           | Required | Purpose                                                              |
| :-------------- | :------- | :------------------------------------------------------------------- |
| `name`          | Yes      | Skill identifier; lowercase, kebab-case, matches the folder name     |
| `description`   | Yes      | What the skill does and the user phrasing that should trigger it     |
| `license`       | No       | SPDX identifier or short license note                                |
| `compatibility` | No       | Run-time requirements (CLI version, Python, env vars)                |
| `allowed-tools` | No       | Tools the skill is permitted to call (Claude Code)                   |
| `metadata`      | No       | Free-form key/value tags                                             |

## Progressive disclosure

A skill's `SKILL.md` is loaded up front so the agent knows it exists.
The body and any `references/` files are loaded only when the skill is
triggered, so a large skill is cheap until it is needed. Keep `SKILL.md`
short: the spec recommends under 500 lines.[^agentskills-spec]

## `references/` subdirectory

A skill may put deeper material under `references/` (for example
`references/exit-codes.md`) and link to it from the body. Each
`references/*.md` carries its own frontmatter and is loaded on demand.

[^agentskills-spec]: Agent Skills specification
