# Exit codes

The `clockify` CLI keeps data on stdout and diagnostics on stderr. Exit codes
are a stable contract.

| Code | Meaning             | What the agent does                                          |
| ---- | ------------------- | ------------------------------------------------------------ |
| 0    | Success             | Continue.                                                    |
| 1    | Unexpected failure  | Report stderr to the user; retry with `-v` once if useful.   |
| 2    | Invalid usage       | Fix the arguments (check `--help`); global options go first. |
| 3    | Configuration error | Run `clockify config list`; ask the user to fix the profile. |
| 4    | Authentication      | Ask the user to run `clockify auth login`; then stop.        |
| 5    | Forbidden           | The key lacks permission; report it, do not retry.           |
| 6    | Not found           | List candidates (`project list`, `task list`) and ask.       |
| 7    | Validation failure  | Correct the rejected field named in stderr.                  |
| 8    | Rate limited        | Wait, then retry once; do not loop.                          |
| 9    | Service unavailable | Report it and retry later.                                   |
