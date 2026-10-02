---
type: reference
title: Invoices
description: How invoice amounts are typed and shown, when the list uses the search endpoint, which changes Clockify does not retry, and how invoice and settings updates keep unchanged fields.
tags: [commands, invoices]
status: stable
---

# Invoices

Invoices are a Standard-plan feature. On a lower plan Clockify answers `403`,
which the CLI reports with exit code 5. The models follow the OpenAPI spec and
were not checked against a real response; see the SDK's `docs/sdk/invoices.md`.

## Amounts

Clockify stores money as an integer count of the currency's minor unit, so
`12000` is `120.00`.

- Options that take an amount (`--unit-price`, `--amount`, `--amount-over`,
  `--amount-under`) take major units such as `120.50`. The CLI rounds half up to
  the minor unit.
- Output keeps Clockify's values, so `-o json` shows `12050`. Table headers say
  `(minor)` to mark the columns that hold minor units.
- Percentages (`--discount`, `--tax`, `--tax2`) are plain numbers.

## Naming an invoice

`INVOICE` takes the invoice ID or its exact number, such as `INV-1`. Resolving a
number lists the workspace's invoices first.

## List and search

Clockify filters by status and sort on one endpoint, and by client, number,
issue date and amount on another. `invoice list` uses the search endpoint only
when one of `--client`, `--number`, `--issued-from`, `--issued-to`,
`--amount-over` or `--amount-under` is given. Both return the same columns.

## Changes that are not retried

Clockify does not retry these on a server error, because a repeat would not be
harmless. Check the invoice with `invoice get` before running one again after a
failure.

- `invoice item delete INVOICE ORDER` removes the item at that position, and the
  items after it are renumbered. A repeat deletes the item that moved up.
- `invoice payment add` records another payment.
- `invoice item add`, `invoice item import` and `invoice duplicate` each add
  something new.

## Updates keep what you leave out

- `invoice update` reads the invoice first, because Clockify's PUT replaces it
  and requires the dates and the three percentages. A date that the stored
  invoice lacks must be passed, or the command exits with code 2.
- `invoice settings update` sends back every stored label, the default notes and
  subject, and the export fields, with only your changes applied. `--label
  NAME=TEXT` renames one label (`NAME` is a snake-case label key, for example
  `due_date`), and `--show` and `--hide` toggle an export field. If Clockify
  returned no value for a label, the command exits with code 2 rather than
  blanking it.

## Export

`invoice export INVOICE --save PATH` writes the file Clockify generates, in the
`--locale` language (default `en`). It follows the rules of
[binary output](expenses.md#binary-data-skips--o): the bytes skip `-o`, an
existing file needs `--force`, and `--save -` streams to a pipe.
