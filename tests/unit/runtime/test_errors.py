from __future__ import annotations

import pytest
import typer
from clockify.errors import AuthenticationError
from clockify.errors import ClockifyAPIError
from clockify.errors import ClockifyError
from clockify.errors import ConflictError
from clockify.errors import ErrorBody
from clockify.errors import ForbiddenError
from clockify.errors import MissingCredentialsError
from clockify.errors import NotFoundError
from clockify.errors import RateLimitError
from clockify.errors import ServerError
from clockify.errors import TransportError
from clockify.errors import ValidationError

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import describe
from clockify_unofficial_cli.runtime.errors import exit_code_for
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (MissingCredentialsError("missing"), ExitCode.CONFIGURATION),
        (AuthenticationError(401), ExitCode.AUTHENTICATION),
        (ForbiddenError(403), ExitCode.FORBIDDEN),
        (NotFoundError(404), ExitCode.NOT_FOUND),
        (ValidationError(400), ExitCode.VALIDATION),
        (ConflictError(409), ExitCode.VALIDATION),
        (RateLimitError(429), ExitCode.RATE_LIMITED),
        (ServerError(503), ExitCode.UNAVAILABLE),
        (TransportError("timeout"), ExitCode.UNAVAILABLE),
        (ClockifyAPIError(418), ExitCode.FAILURE),
    ],
)
def test_sdk_errors_map_to_stable_exit_codes(error: ClockifyError, expected: ExitCode) -> None:
    # Arrange
    sdk_error = error
    # Act
    exit_code = exit_code_for(sdk_error)
    # Assert
    assert exit_code == expected


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (NotFoundError(404, body=ErrorBody(message="Project not found")), "Project not found (HTTP 404)"),
        (ServerError(500), "ServerError (HTTP 500)"),
        (TransportError("connection reset"), "connection reset"),
    ],
)
def test_describe_includes_http_status_when_known(error: ClockifyError, expected: str) -> None:
    # Arrange
    sdk_error = error
    # Act
    description = describe(sdk_error)
    # Assert
    assert description == expected


@handle_errors
def _rate_limited_command() -> None:
    raise RateLimitError(429, body=ErrorBody(message="Too many requests"))


@handle_errors
def _failing_command() -> None:
    message = "boom [not markup]"
    raise CliError(message, exit_code=ExitCode.USAGE)


@handle_errors
def _answer_command() -> int:
    return 42


def test_decorated_command_turns_sdk_error_into_exit(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    command = _rate_limited_command
    # Act
    with pytest.raises(typer.Exit) as caught:
        command()
    # Assert
    assert caught.value.exit_code == ExitCode.RATE_LIMITED
    assert capsys.readouterr().err == (
        "error: Too many requests (HTTP 429)\nhint: Clockify rate limit reached after retries; try again shortly.\n"
    )


def test_decorated_command_turns_cli_error_into_exit(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    command = _failing_command
    # Act
    with pytest.raises(typer.Exit) as caught:
        command()
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
    assert capsys.readouterr().err == "error: boom [not markup]\n"


def test_decorated_command_returns_command_result() -> None:
    # Arrange
    command = _answer_command
    # Act
    result = command()
    # Assert
    assert result == 42
