---
name: clockify-cli
description: >-
  Operate the clockify CLI beyond the timer: authentication and profiles,
  workspaces and users, and managing projects, tasks, tags, clients, user
  groups and custom fields. Use when the user says "clockify login", "switch
  workspace", "create a project", "list tags", "add a client", or asks how to
  use the clockify command.
license: MIT
compatibility: Requires the clockify CLI (clockify-unofficial-cli, Python 3.14+) and a configured Clockify API key
allowed-tools: Bash Read AskUserQuestion
---

# Clockify CLI

Reference for driving the `clockify` CLI. For starting, stopping, logging and
editing time entries, use the `clockify-time-tracking` skill.

## Rules

- Global options MUST come before the subcommand: `-p/--profile`,
  `-w/--workspace`, `-o/--output` (`table|json|jsonl|csv|id`), `-v/--verbose`.
  They also read `CLOCKIFY_PROFILE`, `CLOCKIFY_WORKSPACE` and
  `CLOCKIFY_OUTPUT`.
- MUST pass `-o json` (or `-o id`) when parsing output. Data goes to stdout,
  diagnostics to stderr.
- API keys MUST NOT be passed as arguments or printed. MUST NOT run `clockify
  auth token` unless the user explicitly asks for the raw key.
- Destructive commands (`delete`, `auth logout`) MUST be confirmed with the
  user through `AskUserQuestion` first; pass `--yes` to `delete` only after
  that.
- Names are resolved to IDs by the CLI; an unknown name exits with code 6.
  List the candidates and ask the user.

## Instructions

1. MUST run `clockify --version`. If it is missing, recommend `uv tool
   install clockify-unofficial-cli` or `pipx install clockify-unofficial-cli`
   and stop.
2. Authentication and profiles:
   - `clockify auth login [--region R] [--insecure-storage]` is interactive
     (hidden prompt): the user runs it, not the agent. In CI, the key comes
     from `CLOCKIFY_API_KEY` or `printf '%s' "$KEY" | clockify auth login
     --with-token`.
   - `clockify -o json auth status` shows the user, workspace and credential
     source; exit code 4 means the user must log in.
   - `clockify config path|list` and `clockify config use NAME` inspect and
     select profiles.
3. Workspace and users:
   - `clockify workspace list|get|use` (`use` persists the choice in the
     active profile).
   - `clockify user me|list`.
4. Resource management, each with `clockify <group> <verb> --help`:

   | Group          | Verbs                             | Notes                           |
   | -------------- | --------------------------------- | ------------------------------- |
   | `project`      | list, get, create, update, delete | `get` takes an ID or exact name |
   | `task`         | list, get, create, update, delete | `list` requires `-P PROJECT`    |
   | `tag`          | list, get, create, update, delete |                                 |
   | `client`       | list, get, create, update, delete |                                 |
   | `group`        | list, create, update, delete      | user groups                     |
   | `custom-field` | list, create, update, delete      |                                 |

   Read with `list`/`get` first to confirm the target before `update` or
   `delete`.
5. On a non-zero exit, follow [exit-codes.md](references/exit-codes.md).

Only the commands in `clockify --help` exist; the rest of the Clockify API is
tracked in the project's `docs/coverage.md`.
