---
type: reference
title: Report output
description: How report commands pick a date range, flatten grouped results and keep totals off stdout.
tags: [commands, reports]
status: stable
---

# Report output

`report summary`, `report detailed`, `report weekly` and `shared-report
generate` read from Clockify's reports host through the SDK. The SDK always
asks for JSON, so the CLI has no PDF, CSV or XLSX export from Clockify;
`-o csv` renders the rows locally instead.

## Date range

- `--period` takes `today`, `yesterday`, `this-week`, `last-week`,
  `this-month` or `last-month`. The boundaries are local midnight, converted
  to UTC, and weeks start on Monday. The range ends on the last second of the
  period, because Clockify treats `dateRangeEnd` as inclusive.
- `--from` and `--to` take the same instants as `entry list`. With only
  `--from`, the range ends now. `--to` alone is a usage error.
- `--period` together with `--from` or `--to` is a usage error. With none of
  them, the range is `this-week`.

## Rows and totals

- `summary` and `weekly` return groups that nest, for example user, then
  project. The CLI emits one row per node, with a `level` column (1 is the
  outermost group), so table, CSV and JSON stay uniform and the hierarchy can
  be rebuilt.
- `detailed` emits one row per time entry, with Clockify's own field names.
- The totals line (`Total: 5400s (3600s billable) in 3 entries.`) goes to
  stderr. Stdout carries only the rows, so `-o json` stays parseable. The
  sum of the `level` 1 durations equals the total.
- `shared-report generate` has no fixed columns: a shared report can be of
  any kind, so the columns follow the keys of the payload.
