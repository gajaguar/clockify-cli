from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

STDOUT: Final = "-"


# Binary payloads (receipts, exported invoices) bypass the renderers on purpose: they are not a
# dataset, so `-o json` never applies to them. A path is the default target; `-` streams to a pipe
# and is refused on a terminal, where raw bytes would only corrupt the screen.
def save_bytes(content: bytes, destination: str, *, force: bool = False) -> str:
    if destination == STDOUT:
        if sys.stdout.isatty():
            message = "Refusing to write binary data to a terminal; redirect stdout or pass a file path."
            raise CliError(message, exit_code=ExitCode.USAGE)
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.flush()
        return f"Wrote {len(content)} bytes to stdout."
    path = Path(destination)
    if path.exists() and not force:
        message = f"'{path}' already exists; pass --force to overwrite it."
        raise CliError(message, exit_code=ExitCode.USAGE)
    try:
        path.write_bytes(content)
    except OSError as exc:
        message = f"Cannot write '{path}': {exc.strerror}."
        raise CliError(message, exit_code=ExitCode.FAILURE) from exc
    return f"Saved {len(content)} bytes to {path}."


__all__ = ["STDOUT", "save_bytes"]
