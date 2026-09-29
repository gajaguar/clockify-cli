from __future__ import annotations

import pytest

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.runtime.prompts import confirm


def test_confirm_returns_when_assume_yes() -> None:
    # Arrange
    # Act
    # Assert
    confirm("delete thing", assume_yes=True)


def test_confirm_raises_usage_when_non_tty_without_assume_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr("clockify_unofficial_cli.runtime.prompts.sys.stdin.isatty", lambda: False)
    # Act
    with pytest.raises(CliError) as caught:
        confirm("delete thing", assume_yes=False)
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
    assert "requires --yes" in caught.value.message
