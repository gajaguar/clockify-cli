from __future__ import annotations

import datetime

import pytest

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.parsing import parse_duration
from clockify_unofficial_cli.services.parsing import parse_instant


def test_parse_duration_with_hours_and_minutes() -> None:
    # Arrange
    value = "1h30m"
    # Act
    result = parse_duration(value)
    # Assert
    assert result == datetime.timedelta(hours=1, minutes=30)


def test_parse_duration_with_only_minutes() -> None:
    # Arrange
    value = "90m"
    # Act
    result = parse_duration(value)
    # Assert
    assert result == datetime.timedelta(minutes=90)


def test_parse_duration_with_clock_format() -> None:
    # Arrange
    value = "1:30"
    # Act
    result = parse_duration(value)
    # Assert
    assert result == datetime.timedelta(hours=1, minutes=30)


def test_parse_duration_with_clock_format_with_seconds() -> None:
    # Arrange
    value = "1:30:45"
    # Act
    result = parse_duration(value)
    # Assert
    assert result == datetime.timedelta(hours=1, minutes=30, seconds=45)


def test_parse_duration_rejects_invalid_input() -> None:
    # Arrange
    value = "not-a-duration"
    # Act
    with pytest.raises(CliError) as caught:
        parse_duration(value)
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE


def test_parse_instant_with_iso_format() -> None:
    # Arrange
    value = "2026-09-17T09:00"
    # Act
    result = parse_instant(value)
    # Assert
    assert result == datetime.datetime(2026, 9, 17, 9, 0, tzinfo=datetime.UTC)


def test_parse_instant_with_clock_only() -> None:
    # Arrange
    value = "09:00"
    # Act
    result = parse_instant(value)
    # Assert
    assert result.tzinfo == datetime.UTC
    assert result.hour == 9
    assert result.minute == 0


def test_parse_instant_with_relative_offset() -> None:
    # Arrange
    value = "-2h"
    # Act
    before = datetime.datetime.now(datetime.UTC)
    result = parse_instant(value)
    after = datetime.datetime.now(datetime.UTC)
    # Assert
    expected_low = before - datetime.timedelta(hours=2, seconds=1)
    expected_high = after - datetime.timedelta(hours=2) + datetime.timedelta(seconds=1)
    assert expected_low <= result <= expected_high


def test_parse_instant_with_yesterday_keyword() -> None:
    # Arrange
    value = "yesterday 09:00"
    # Act
    result = parse_instant(value)
    # Assert
    today = datetime.datetime.now(datetime.UTC).date()
    assert result.date() == today - datetime.timedelta(days=1)
    assert result.hour == 9
    assert result.minute == 0


def test_parse_instant_with_today_keyword() -> None:
    # Arrange
    value = "today"
    # Act
    result = parse_instant(value)
    # Assert
    today = datetime.datetime.now(datetime.UTC).date()
    assert result.date() == today


def test_parse_instant_rejects_invalid_input() -> None:
    # Arrange
    value = "not-a-time"
    # Act
    with pytest.raises(CliError) as caught:
        parse_instant(value)
    # Assert
    assert caught.value.exit_code == ExitCode.USAGE
