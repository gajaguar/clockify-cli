from __future__ import annotations

import io
from typing import TYPE_CHECKING
from typing import override

import pytest

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.files import save_bytes

if TYPE_CHECKING:
    from pathlib import Path


class _Terminal(io.TextIOWrapper):
    @override
    def isatty(self) -> bool:
        return True


def test_save_bytes_refuses_a_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr("sys.stdout", _Terminal(io.BytesIO()))
    # Act
    with pytest.raises(CliError) as caught:
        save_bytes(b"binary", "-")
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE


def test_save_bytes_writes_a_new_file(tmp_path: Path) -> None:
    # Arrange
    target = tmp_path / "receipt.bin"
    # Act
    message = save_bytes(b"abc", str(target))
    # Assert
    assert (target.read_bytes(), message) == (b"abc", f"Saved 3 bytes to {target}.")
