from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING
from typing import Final

import typer
from clockify.errors import AuthenticationError
from clockify.errors import ClockifyAPIError
from clockify.errors import ClockifyError
from clockify.errors import ConfigurationError
from clockify.errors import ConflictError
from clockify.errors import ForbiddenError
from clockify.errors import NotFoundError
from clockify.errors import RateLimitError
from clockify.errors import ServerError
from clockify.errors import TransportError
from clockify.errors import ValidationError
from rich.console import Console
from rich.markup import escape

from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable


class CliError(Exception):
    def __init__(self, message: str, *, exit_code: ExitCode = ExitCode.FAILURE, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.hint = hint


# Ordered most-specific first: the first isinstance match wins.
_SDK_EXIT_CODES: Final[tuple[tuple[type[ClockifyError], ExitCode], ...]] = (
    (ConfigurationError, ExitCode.CONFIGURATION),
    (AuthenticationError, ExitCode.AUTHENTICATION),
    (ForbiddenError, ExitCode.FORBIDDEN),
    (NotFoundError, ExitCode.NOT_FOUND),
    (ValidationError, ExitCode.VALIDATION),
    (ConflictError, ExitCode.VALIDATION),
    (RateLimitError, ExitCode.RATE_LIMITED),
    (ServerError, ExitCode.UNAVAILABLE),
    (TransportError, ExitCode.UNAVAILABLE),
)

_SDK_HINTS: Final[dict[ExitCode, str]] = {
    ExitCode.AUTHENTICATION: "Run `clockify auth login` to store a valid API key.",
    ExitCode.RATE_LIMITED: "Clockify rate limit reached after retries; try again shortly.",
}


def exit_code_for(error: ClockifyError) -> ExitCode:
    for error_type, exit_code in _SDK_EXIT_CODES:
        if isinstance(error, error_type):
            return exit_code
    return ExitCode.FAILURE


def describe(error: ClockifyError) -> str:
    detail = error.message or type(error).__name__
    if isinstance(error, ClockifyAPIError) and error.status_code:
        return f"{detail} (HTTP {error.status_code})"
    return detail


def report(message: str, hint: str | None = None) -> None:
    console = Console(stderr=True, highlight=False)
    console.print(f"[bold red]error:[/] {escape(message)}")
    if hint:
        console.print(f"[dim]hint:[/] {escape(hint)}")


def handle_errors[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except CliError as error:
            report(error.message, error.hint)
            raise typer.Exit(error.exit_code) from error
        except ClockifyError as error:
            exit_code = exit_code_for(error)
            report(describe(error), _SDK_HINTS.get(exit_code))
            raise typer.Exit(exit_code) from error

    return wrapper
