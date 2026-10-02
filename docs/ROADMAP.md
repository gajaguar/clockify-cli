---
type: playbook
title: Roadmap
description: How the CLI reached 1.0.0 by covering everything the SDK offers, and what waits for SDK support afterwards.
tags: [roadmap, release]
status: stable
---

# Roadmap

`1.0.0` exposes **every Clockify operation that `clockify-unofficial-sdk`
`1.10` offers**: 105 of the 166 non-deprecated operations in Clockify's
[OpenAPI document](https://docs.clockify.me/openapi.json). The other 61 have no
SDK method yet, so the CLI cannot reach them (see
[Reached through the SDK first](#reached-through-the-sdk-first)).
[`coverage.md`](coverage.md) holds the row-by-row mapping and status, and
`make coverage-report` measures it against the live spec.

## Releases to 1.0.0

Each release added one area, and raised the SDK floor when it needed a newer
SDK. The CLI is versioned with SemVer: a new command group is a minor release.
`0.2.0` was the first tagged release.

| CLI release | Area                                                    | New operations | Cumulative      | SDK floor |
| ----------- | ------------------------------------------------------- | -------------- | --------------- | --------- |
| `0.2.0`     | Foundation, workspaces, users, projects, tasks, entries | 39             | 39 / 166 (23%)  | —         |
| `0.3.0`     | Group membership, webhooks                              | 11             | 50 / 166 (30%)  | `1.10`    |
| `0.4.0`     | Reports                                                 | 4              | 54 / 166 (33%)  | `1.10`    |
| `0.5.0`     | Time off, approvals                                     | 23             | 77 / 166 (46%)  | `1.10`    |
| `0.6.0`     | Expenses and receipts                                   | 11             | 88 / 166 (53%)  | `1.10`    |
| `0.7.0`     | Invoices                                                | 17             | 105 / 166 (63%) | `1.10`    |
| `1.0.0`     | Stability: the contracts below are frozen               | 0              | 105 / 166 (63%) | `1.10`    |

Releases from `0.3.0` on are Git tags. The package is published to PyPI by
creating a GitHub release for a tag; see
[`toolchain/releasing.md`](toolchain/releasing.md).

## What 1.0.0 freezes

From `1.0.0` a breaking change needs a major version. The contract is:

- **Exit codes.** The values in
  [Errors and exit codes](ARCHITECTURE.md#errors-and-exit-codes). A new failure
  reuses an existing code, and a new code is added without renumbering.
- **JSON output.** `-o json` and `jsonl` keep Clockify's camelCase field names.
  Removing or renaming a field, or changing its type, is breaking; adding a
  field is not. The `id` and `csv` formats keep their shape.
- **Streams.** Rendered data goes to stdout. Prompts, totals, progress and
  errors go to stderr. Binary downloads go only to the file or stream named by
  `--save`.
- **Command surface.** The `clockify <noun> <verb>` grammar, the commands and
  options in `coverage.md` that are `done`, the global options and their
  environment variables, and the keys of `config.toml`.

These are **not** frozen: table layout and column headers, the text of messages
and `--help`, and the order of rows that Clockify does not sort.

## Reached through the SDK first

Every area below is missing from the SDK, so the CLI cannot expose it. Each
needs the SDK to add the method before the CLI adds the command, following the
[cross-repo workflow](#cross-repo-workflow). The commands are listed in
`coverage.md` as `planned` and arrive in `1.x` minor releases.

| Area                          | Operations | CLI additions                                                                                                                      |
| ----------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Workspace                     | 8          | `workspace create`, billable and cost rates, invite users, limited users, user status and rates                                    |
| Users                         | 8          | `user set-photo`, `user profile get/update`, `user search`, `user set-field`, `user managers`, `user grant-manager/revoke-manager` |
| Projects                      | 7          | create from template, estimate, memberships, template flag, per-user rates                                                         |
| Tasks                         | 2          | task billable and cost rates                                                                                                       |
| Custom fields                 | 3          | project-level custom fields                                                                                                        |
| Time entries                  | 6          | batch get, mark invoiced, running entries for all users, bulk delete, bulk update, `entry duplicate` and `continue`                |
| Reports                       | 7          | `report attendance`, `report expenses`, `report audit-log`, and `shared-report list/create/update/delete`                          |
| Holidays                      | 5          | `holiday list/create/update/delete`                                                                                                |
| Approvals                     | 1          | `approval resubmit --user`                                                                                                         |
| Scheduling                    | 11         | `schedule list/create/update/delete`, recurrence, copy, publish, totals and capacity                                               |
| Entity changes (experimental) | 3          | `changes created/updated/deleted --since`                                                                                          |

Besides endpoints, three improvements were left for after `1.0.0`:

- a scheduled job that runs `make openapi-fetch coverage-report` and opens an
  issue when Clockify changes its API;
- a command reference generated from Typer
  (`typer clockify_unofficial_cli.main utils docs`) and a recipes page;
- third-party command groups through a `clockify_unofficial_cli.plugins`
  entry-point group.

## Cross-repo workflow

An area that needs a new SDK capability goes through both repositories in the
same order:

1. **SDK.** Implement the endpoints in `clockify-sdk`, following its
   `docs/ARCHITECTURE.md` "Adding a new endpoint" steps:
   - models;
   - a resource method with a `# METHOD /path` comment and a CQS kind;
   - respx tests;
   - its own `coverage.md` rows.

   Then tag the release.
2. **Pin.** Raise the `clockify-unofficial-sdk` floor in the CLI's
   `pyproject.toml` to the released version and run `uv lock`.
3. **CLI.** Add the commands and services, following
   [`ARCHITECTURE.md`](ARCHITECTURE.md#adding-a-command). Flip the
   `coverage.md` rows to `done`.
4. **Gate.** `make check && make test && make coverage-report` must pass.
   Then tag the CLI release.

An area is **done** when:

- every row assigned to it is `done` in both coverage tables;
- each new command has a success test, a JSON-output test and a failure
  exit-code test;
- the SDK floor in `pyproject.toml` is the release that added it.

## Deprecated endpoints

Nine operations are marked `deprecated` in the spec and are excluded from the
166:

- legacy approval submission (2);
- the `GET` scheduling project totals (1);
- templates (5);
- `DELETE /workspaces/{workspaceId}/users/{userId}` (1).

Each one has a non-deprecated replacement. Revisit this list when Clockify
removes or restores any of them.

## Risks

| Risk                                                                             | Mitigation                                                                                                        |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Upstream API changes after release                                               | `make coverage-report` flags new or removed operations; a scheduled job to run it is on the list above.           |
| Plan-gated features (time off, invoices, expenses, scheduling) are untested live | Contract tests use respx with payloads built from the OpenAPI schemas; live smoke tests cover only the free plan. |
| SDK and CLI release drift                                                        | The CLI sets a SDK floor, and an area only closes when both coverage tables agree.                                |
| Large command surface hurts discoverability                                      | Consistent noun-verb grammar, shell completion, and a generated command reference on the list above.              |
