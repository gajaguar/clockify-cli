from __future__ import annotations

import sys

import typer

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode


# Single "are you sure?" prompt shared by every destructive command.
# TTYs get an interactive confirm; non-TTY callers must pass --yes. A "no" reply
# exits OK (the user explicitly cancelled, not a failure).
def confirm(action: str, *, assume_yes: bool) -> None:
    if assume_yes:
        return
    if not sys.stdin.isatty():
        message = f"{action} requires --yes when run non-interactively."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if not typer.confirm(action, err=True):
        raise typer.Exit(ExitCode.OK)


__all__ = ["confirm"]
