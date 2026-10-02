---
name: clockify-cli
description: >-
  Operate the clockify CLI beyond the timer: authentication and profiles,
  workspaces and users, managing projects, tasks, tags, clients, user
  groups, custom fields and webhooks, reporting tracked time, time off,
  approvals, expenses and invoices. Use when the user says "clockify login", "switch
  workspace", "create a project", "list tags", "add a client", "time report", "request time off", "approve a timesheet", "log an expense", "create an invoice", or asks how to
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

   | Group          | Verbs                                                           | Notes                                                                      |
   | -------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
   | `project`      | list, get, create, update, delete                               | `get` takes an ID or exact name                                            |
   | `task`         | list, get, create, update, delete                               | `list` requires `-P PROJECT`                                               |
   | `tag`          | list, get, create, update, delete                               |                                                                            |
   | `client`       | list, get, create, update, delete                               |                                                                            |
   | `group`        | list, create, update, delete, add-user, remove-user             | user groups                                                                |
   | `webhook`      | list, get, create, update, delete, rotate-token, logs, statuses | `create` and `rotate-token` print the signing token; `list`/`get` never do |
   | `custom-field` | list, create, update, delete                                    |                                                                            |

   Reports: `clockify report summary|detailed|weekly` take `--period
   today|yesterday|this-week|last-week|this-month|last-month` or `--from/--to`,
   plus `-P`, `--client`, `--tag` and `--user` filters. Rows go to stdout, the
   totals line to stderr. `clockify shared-report generate REPORT` opens a
   shared report.

   Time off: `clockify time-off policy|request|balance ...` and approvals:
   `clockify approval list|submit|resubmit|approve|reject|withdraw`. Balance
   changes (`balance update --value`, `update-assignment --change`) are deltas
   and are not retried, so never repeat one blindly. These need a Standard
   plan; exit code 5 means the plan or role does not allow it.

   Expenses: `clockify expense list|get|create|update|delete|receipt` and
   `clockify expense category ...`. `--receipt FILE` uploads a receipt and
   `receipt EXPENSE --save PATH` downloads it; binary data skips `-o` and
   refuses to overwrite without `--force`. Expenses need a Pro plan.

   Invoices: `clockify invoice list|get|create|update|delete|duplicate|export|
   set-status`, plus `invoice item`, `invoice payment` and `invoice settings`.
   Amounts are typed in major units (`120.50`) but shown in minor units.
   `invoice item delete` renumbers the items and `invoice payment add` is not
   idempotent, so never repeat either blindly.

   Read with `list`/`get` first to confirm the target before `update` or
   `delete`.
5. On a non-zero exit, follow [exit-codes.md](references/exit-codes.md).

Only the commands in `clockify --help` exist; the rest of the Clockify API is
tracked in the project's `docs/coverage.md`.
