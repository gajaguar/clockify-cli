---
type: reference
title: Expenses and binary output
description: How expense receipts are uploaded and downloaded, why binary data skips the output formats, and how expense and category updates keep unchanged fields.
tags: [commands, expenses, output]
status: stable
---

# Expenses and binary output

Expenses are a Pro-plan feature. On a lower plan Clockify answers `403`, which
the CLI reports with exit code 5. The models follow the OpenAPI spec and were
not checked against a real response; see the SDK's
`docs/sdk/multipart-uploads.md` and `docs/sdk/binary-downloads.md`.

## Receipts

- `expense create` and `expense update` send `multipart/form-data`.
  `--receipt FILE` reads the whole file into memory and guesses its content
  type from the file name. A file that does not exist is a usage error.
- `expense receipt EXPENSE --save PATH` downloads the receipt. The receipt ID
  comes from the expense unless `--file-id` is given; an expense without one
  exits with code 6.

## Binary data skips `-o`

A receipt is bytes, not a dataset, so `-o json`, `csv` and the other formats do
not apply to it. The same rule holds for any later command that downloads a
file, such as the invoice export.

- `--save PATH` writes the file and prints `Saved N bytes to PATH.` to stderr.
- It refuses to replace an existing file unless `--force` is given.
- `--save -` writes the bytes to stdout, so it can feed a pipe. It is refused
  on a terminal, where raw bytes would only corrupt the screen.
- A destination that cannot be written exits with code 1.

## Updates keep what you leave out

- `expense update` reads the stored expense and sends `changeFields` with only
  the options you passed. Clockify still wants the user, category, date and
  amount, so those are copied from the stored expense. Passing no option is a
  usage error. `--task` needs a project, from `--project` or the stored one.
- `expense category update` reads the category from the list, because Clockify
  has no endpoint for one category, and keeps its unit and price when you do
  not change them.
- `--unit-price` takes major currency units (`0.58`) and sends cents (`58`).
  Setting it marks the category as priced.
