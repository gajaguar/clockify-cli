---
type: playbook
title: Managing installed skills
description: npx skills list, update, and remove — the day-to-day commands after an install.
tags: [agents, npx-skills]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-29T00:00:00Z }
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: vercel-skills
    resource: https://github.com/vercel-labs/skills
    title: vercel-labs/skills (the `npx skills` CLI)
    author: team:vercel-labs
---

# Managing installed skills

`npx skills` ships three management commands; the install command is
covered in [`npx-skills-install.md`](npx-skills-install.md).[^vercel-skills]

## List what is installed

```bash
npx skills list
```

Lists every skill the CLI copied into any of the per-agent paths it
manages. Pass `-a` to scope to one agent.

## Update

```bash
npx skills update
```

Re-reads each tracked source repository and overwrites the local files
when the source changed. There is no auto-update; run this after a
release or a CI bump.

## Remove

```bash
npx skills remove
```

Removes the skills from every per-agent path they were installed to.
The source repository is untouched.

[^vercel-skills]: vercel-labs/skills (the `npx skills` CLI)
