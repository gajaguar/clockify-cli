from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from clockify import ExpenseFile

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.expenses import read_receipt

if TYPE_CHECKING:
    from pathlib import Path


def test_read_receipt_guesses_the_content_type(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "taxi.pdf"
    path.write_bytes(b"%PDF")
    # Act
    receipt = read_receipt(path)
    # Assert
    assert receipt == ExpenseFile(filename="taxi.pdf", content=b"%PDF", content_type="application/pdf")


def test_read_receipt_reports_an_unreadable_file(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "missing.pdf"
    # Act
    with pytest.raises(CliError) as caught:
        read_receipt(path)
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
