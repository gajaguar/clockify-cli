---
name: clockify-time-tracking
description: >-
  Track time in Clockify with the clockify CLI: start, stop and inspect the
  running timer, log finished entries, and list, update or delete time
  entries. Use when the user says "start a timer", "stop tracking", "log 2h on
  project X", "what am I tracking", "my time entries today", or asks to fix a
  Clockify entry.
license: MIT
compatibility: Requires the clockify CLI (clockify-unofficial-cli, Python 3.14+) and a configured Clockify API key
allowed-tools: Bash Read AskUserQuestion
---

# Clockify time tracking

Drive the `clockify` CLI to record and review time. The CLI owns name-to-ID
resolution, output formatting and exit codes; this skill only chooses the
right command and flags.

## Rules

- Global options (`-p`, `-w`, `-o`, `-v`) MUST come before the subcommand:
  `clockify -o json entry list`, never `clockify entry list -o json`.
- MUST pass `-o json` (or `-o id`) whenever the output is parsed. Data is on
  stdout, diagnostics on stderr.
- MUST NOT ask for, print or pass the API key, and MUST NOT run `clockify
  auth token`. The user logs in themselves.
- `--project` and `--task` accept an ID or an exact name; `--task` requires
  `--project`. `--tag` may be repeated.
- Instants are read as UTC when no offset is given. Accepted forms: ISO
  (`2026-09-17T09:00`), `HH:MM` (today), `today|yesterday|tomorrow [HH:MM]`,
  and relative `-30m` / `+1h`.
- Durations are `1h30m`, `45m`, `90s` or `1:30`.

## Instructions

1. MUST run `clockify --version`. If it is missing, recommend `uv tool
   install clockify-unofficial-cli` or `pipx install clockify-unofficial-cli`
   and stop.
2. MUST run `clockify -o json auth status`. On exit code 4, tell the user to
   run `clockify auth login` (interactive, hidden prompt) and stop.
3. Choose the workflow:

   | Goal                   | Command                                                                                         |
   | ---------------------- | ----------------------------------------------------------------------------------------------- |
   | What is running?       | `clockify -o json status`                                                                       |
   | Start a timer          | `clockify start [-P PROJECT] [-t TASK] [--tag TAG]... [--billable] [--from INSTANT]`            |
   | Stop the timer         | `clockify stop`                                                                                 |
   | Log a finished entry   | `clockify log --duration 1h30m` or `--from A --to B`, plus `--description`, `-P`, `-t`, `--tag` |
   | List entries           | `clockify -o json entry list [--from] [--to] [-P] [-t] [--tag] [--description] [--limit N]`     |
   | Show / update / delete | `clockify entry get ID`, `entry update ID`, `entry delete ID`                                   |

   `log` takes `--duration` with one of `--from`/`--to`, or both `--from`
   and `--to`.
4. `entry update` replaces the entry and REQUIRES `--from`. MUST read the
   entry first with `entry get ID` and pass along every field that should
   stay unchanged.
5. `entry delete` prompts for confirmation. MUST ask the user with
   `AskUserQuestion` first, and only then pass `--yes`.
6. If a project, task or tag is reported as unknown (exit code 6), list the
   candidates with `clockify -o json project list` (or `task list -P
   PROJECT`, `tag list`) and ask the user which one they meant.
7. On any other non-zero exit, follow
   [exit-codes.md](references/exit-codes.md).

Run `clockify <command> --help` for flags not listed here.
