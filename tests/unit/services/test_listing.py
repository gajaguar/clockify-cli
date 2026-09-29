from __future__ import annotations

from dataclasses import dataclass

import pytest

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.listing import ListOptions
from clockify_unofficial_cli.services.listing import collect


@dataclass(frozen=True, slots=True)
class FakePage:
    items: list[str]


def test_collect_returns_all_when_no_options_given() -> None:
    # Arrange
    options = ListOptions()
    # Act
    result = list(collect(lambda: iter(["a", "b", "c"]), lambda **_: FakePage(items=[]), options))
    # Assert
    assert result == ["a", "b", "c"]


def test_collect_truncates_to_limit() -> None:
    # Arrange
    options = ListOptions(limit=2)
    # Act
    result = list(collect(lambda: iter(["a", "b", "c"]), lambda **_: FakePage(items=[]), options))
    # Assert
    assert result == ["a", "b"]


def test_collect_returns_one_page_when_page_size_given() -> None:
    # Arrange
    options = ListOptions(page=2, page_size=10)
    # Act
    result = list(collect(lambda: iter(["a"]), lambda **kwargs: FakePage(items=["p"]), options))
    # Assert
    assert result == ["p"]


def test_collect_rejects_combining_limit_with_pagination() -> None:
    # Arrange
    options = ListOptions(limit=1, page=1)
    # Act
    with pytest.raises(CliError) as caught:
        list(collect(lambda: iter([]), lambda **_: FakePage(items=[]), options))
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
