# Roadmap

Phased plan to expose **100% of Clockify's non-deprecated API operations**
through the CLI. Operation counts come from Clockify's
[OpenAPI document](https://docs.clockify.me/openapi.json): 175 operations, of
which 166 aren't deprecated. [`coverage.md`](coverage.md) holds the
row-by-row mapping and status, and `make coverage-report` measures progress
against the live spec.

## Summary

| Phase | Theme                                | SDK release         | New operations | Cumulative       | CLI release |
| ----- | ------------------------------------ | ------------------- | -------------- | ---------------- | ----------- |
| 0     | Foundation                           | —                   | 0              | 0 / 166 (0%)     | `0.1.0`     |
| 1     | MVP on the current SDK               | `v0.1.0` (existing) | 39             | 39 / 166 (23%)   | `0.2.0`     |
| 2     | Core completion                      | `v0.2.0`            | 36             | 75 / 166 (45%)   | `0.3.0`     |
| 3     | Reports                              | `v0.3.0`            | 11             | 86 / 166 (52%)   | `0.4.0`     |
| 4     | Time off, holidays, approvals        | `v0.4.0`            | 29             | 115 / 166 (69%)  | `0.5.0`     |
| 5     | Expenses and invoices                | `v0.5.0`            | 28             | 143 / 166 (86%)  | `0.6.0`     |
| 6     | Scheduling, webhooks, entity changes | `v0.6.0`            | 23             | 166 / 166 (100%) | `0.7.0`     |
| 7     | Release hardening                    | `v1.0.0`            | —              | 166 / 166        | `1.0.0`     |

## Cross-repo workflow

Every phase after Phase 1 goes through both repositories in the same order:

1. **SDK.** Implement the phase's endpoints in `clockify-sdk`, following its
   `docs/ARCHITECTURE.md` "Adding a new endpoint" steps:
   - models;
   - a resource method with a `# METHOD /path` comment and a CQS kind;
   - respx tests;
   - its own `coverage.md` rows.

   Then tag the release.
2. **Pin.** Bump the `clockify-unofficial-sdk` tag in the CLI's
   `[tool.uv.sources]` and run `uv lock`.
3. **CLI.** Add the commands and services, following
   [`ARCHITECTURE.md`](ARCHITECTURE.md#adding-a-command). Flip the
   `coverage.md` rows to `done`.
4. **Gate.** `make check && make test && make coverage-report` must pass.
   Then tag the CLI release.

A phase is **done** when:

- every row assigned to it is `done` in both coverage tables;
- each new command has a success test, a JSON-output test and a failure
  exit-code test;
- the SDK tag pinned in `pyproject.toml` is the phase's release.

## Phase 0 — Foundation

**Status: done.**

- Instantiated `project-template@python`: package `clockify_unofficial_cli`, console
  script `clockify`.
- Root app with global options (`--profile`, `--workspace`, `--output`,
  `--version`) and shell completion.
- `AppContext` with a lazy client factory, and `create_app(services_factory)`
  for dependency injection in tests.
- Credential stores (environment, keyring, opt-in `0600` file) with a
  precedence chain; `auth login|status|logout|token`.
- `config.toml` settings with profiles; `config path|list|use`.
- Renderers: `table`, `json`, `jsonl`, `csv` and `id`.
- Error adapter with the exit-code contract.
- `scripts/coverage_report.py`, `make openapi-fetch` and
  `make coverage-report`.

## Phase 1 — MVP on the current SDK (39 operations)

**Status: done.**

- **Commands:**
  - `workspace list|get|use` (`use` writes the profile's `workspace_id`);
  - `user me|list`;
  - `client`, `project`, `task` and `tag` CRUD;
  - `custom-field list|create|update|delete`;
  - `group list|create|update|delete`;
  - `entry list|get|create|update|delete`.
- **Timer shortcuts:** `start [DESCRIPTION] -P PROJECT -t TASK --tag ...`,
  `stop`, `status` (the running entry) and `log` (a finished entry with
  `--from/--to` or `--duration`).
- **Services:**
  - `services/resolve.py`: name-or-ID lookup with an ambiguity error;
  - `services/timer.py`;
  - `services/parsing.py`: durations and relative dates in the local
    timezone, converted to UTC.
- **Cross-cutting:**
  - `--yes` confirmation for deletes;
  - `--limit`, `--page` and `--page-size` mapped to the SDK's `list()` and
    `list_page()`;
  - `--verbose` for request diagnostics.

## Phase 2 — Core completion (36 operations)

**SDK `v0.2.0`** adds the remaining core operations. **CLI** adds the
matching commands.

| Area          | Operations | CLI additions                                                                                                                      |
| ------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Workspace     | 8          | `workspace create`, billable/cost rates, invite users, limited users, user status and rates                                        |
| Users         | 8          | `user set-photo`, `user profile get/update`, `user search`, `user set-field`, `user managers`, `user grant-manager/revoke-manager` |
| Projects      | 7          | create from template, estimate, memberships, template flag, per-user rates                                                         |
| Tasks         | 2          | task billable and cost rates                                                                                                       |
| Custom fields | 3          | project-level custom fields                                                                                                        |
| Time entries  | 6          | batch get, mark invoiced, running entries for all users, bulk delete, bulk update, `entry duplicate` / `continue`                  |
| User groups   | 2          | `group add-user`, `group remove-user`                                                                                              |

## Phase 3 — Reports (11 operations)

**SDK `v0.3.0`:**

- Reports API resources on the reports host: detailed, summary, weekly,
  attendance, expenses and audit log.
- Shared reports CRUD and generate.
- Request models for filters and grouping.

**CLI:**

- `report detailed|summary|weekly|attendance|expenses|audit-log`.
- Date-range presets (`--today`, `--this-week`, `--last-month`,
  `--from/--to`), grouping options and `--export FILE` (CSV, JSON, or the
  API's native PDF/XLSX where offered).
- `shared-report list|create|update|delete|generate`.

## Phase 4 — Time off, holidays, approvals (29 operations)

**SDK `v0.4.0`** adds the time-off resources: policies (6), requests (5),
balances (3), balance assignments (4), holidays (5) and approvals (6).

**CLI** adds:

- `time-off policy …`, `time-off request …` and `time-off balance …`;
- `holiday …`;
- `approval list|submit|resubmit|approve|reject|withdraw`.

## Phase 5 — Expenses and invoices (28 operations)

**SDK `v0.5.0`** adds expenses and categories (11), plus invoices with
items, payments, settings and export (17). It also needs multipart upload
(receipts) and binary download (receipts, invoice export).

**CLI** adds:

- `expense …` with `--receipt FILE` and `receipt --save FILE`;
- `expense category …`;
- `invoice …`, `invoice item …`, `invoice payment …` and
  `invoice settings …`;
- `invoice export --save FILE`.

## Phase 6 — Scheduling, webhooks, entity changes (23 operations)

**SDK `v0.6.0`** adds:

- scheduling assignments: CRUD, recurrence, copy, publish and totals (11);
- webhooks: CRUD, token rotation, logs and statuses (9);
- experimental entity-change feeds (3).

**CLI** adds `schedule …`, `webhook …` and
`changes created|updated|deleted --since`. The entity-change commands are
marked experimental in `--help`.

## Phase 7 — Release hardening (`1.0.0`)

- **CI:** enable the template's GitHub Actions workflow (`make check`,
  `make test`) for both repositories. Add a scheduled
  `make openapi-fetch coverage-report` job so upstream API changes open an
  issue.
- **Distribution:** publish both packages to PyPI; document
  `uv tool install clockify-unofficial-cli` and `pipx`.
- **Docs:** a command reference generated from Typer
  (`typer clockify_unofficial_cli.main utils docs`) and a recipes page.
- **Extensibility:** third-party command groups through the
  `clockify_unofficial_cli.plugins` entry-point group.
- **Stability:** freeze the exit-code and JSON output contracts. Breaking
  changes after this point need a major version.

## Deprecated endpoints

Nine operations are marked `deprecated` in the spec and are excluded from
the 100% target:

- legacy approval submission (2);
- the `GET` scheduling project totals (1);
- templates (5);
- `DELETE /workspaces/{workspaceId}/users/{userId}` (1).

Each one has a non-deprecated replacement that is covered. Phase 7 revisits
this list in case upstream removes or restores any of them.

## Risks

| Risk                                                                      | Mitigation                                                                                                          |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Upstream API changes during delivery                                      | `make coverage-report` flags new or removed operations. From Phase 7, a scheduled CI job runs it.                   |
| Plan-gated features (time off, invoices, scheduling) can't be tested live | respx contract tests built from the OpenAPI schemas; live smoke tests only where a suitable workspace is available. |
| SDK and CLI release drift                                                 | The CLI pins an exact SDK tag, and a phase only closes when both coverage tables agree.                             |
| Large command surface hurts discoverability                               | Consistent noun–verb grammar, shell completion and a generated command reference.                                   |
