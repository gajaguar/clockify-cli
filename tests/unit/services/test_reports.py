from __future__ import annotations

import datetime
from typing import Final

import pytest
from clockify import ReportGroupRow
from clockify import ReportTotals

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.reports import DateRange
from clockify_unofficial_cli.services.reports import Period
from clockify_unofficial_cli.services.reports import ReportSelection
from clockify_unofficial_cli.services.reports import describe_totals
from clockify_unofficial_cli.services.reports import flatten_groups
from clockify_unofficial_cli.services.reports import resolve_range

# A Wednesday, so "this-week" starts two days earlier and "last-week" a week before that.
NOW: Final = datetime.datetime(2026, 9, 16, 15, 30, tzinfo=datetime.UTC)


def _utc(*parts: int) -> datetime.datetime:
    return datetime.datetime(*parts, tzinfo=datetime.UTC)


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        (Period.TODAY, DateRange(_utc(2026, 9, 16), _utc(2026, 9, 16, 23, 59, 59))),
        (Period.YESTERDAY, DateRange(_utc(2026, 9, 15), _utc(2026, 9, 15, 23, 59, 59))),
        (Period.THIS_WEEK, DateRange(_utc(2026, 9, 14), _utc(2026, 9, 20, 23, 59, 59))),
        (Period.LAST_WEEK, DateRange(_utc(2026, 9, 7), _utc(2026, 9, 13, 23, 59, 59))),
        (Period.THIS_MONTH, DateRange(_utc(2026, 9, 1), _utc(2026, 9, 30, 23, 59, 59))),
        (Period.LAST_MONTH, DateRange(_utc(2026, 8, 1), _utc(2026, 8, 31, 23, 59, 59))),
    ],
)
def test_resolve_range_expands_each_period_preset(period: Period, expected: DateRange) -> None:
    # Arrange
    selection = ReportSelection(period=period)
    # Act
    result = resolve_range(selection, now=NOW)
    # Assert
    assert result == expected


def test_resolve_range_defaults_to_this_week() -> None:
    # Arrange
    selection = ReportSelection()
    # Act
    result = resolve_range(selection, now=NOW)
    # Assert
    assert result == DateRange(_utc(2026, 9, 14), _utc(2026, 9, 20, 23, 59, 59))


def test_resolve_range_last_month_wraps_the_year() -> None:
    # Arrange
    january = datetime.datetime(2027, 1, 10, tzinfo=datetime.UTC)
    # Act
    result = resolve_range(ReportSelection(period=Period.LAST_MONTH), now=january)
    # Assert
    assert result == DateRange(_utc(2026, 12, 1), _utc(2026, 12, 31, 23, 59, 59))


def test_resolve_range_uses_explicit_bounds() -> None:
    # Arrange
    selection = ReportSelection(start="2026-09-01", end="2026-09-05")
    # Act
    result = resolve_range(selection, now=NOW)
    # Assert
    assert result == DateRange(_utc(2026, 9, 1), _utc(2026, 9, 5))


def test_resolve_range_ends_now_when_only_from_is_given() -> None:
    # Arrange
    selection = ReportSelection(start="2026-09-01")
    # Act
    result = resolve_range(selection, now=NOW)
    # Assert
    assert result == DateRange(_utc(2026, 9, 1), NOW)


@pytest.mark.parametrize(
    "selection",
    [
        ReportSelection(period=Period.TODAY, start="2026-09-01"),
        ReportSelection(end="2026-09-05"),
        ReportSelection(start="2026-09-05", end="2026-09-01"),
    ],
)
def test_resolve_range_rejects_inconsistent_input(selection: ReportSelection) -> None:
    # Arrange
    expected = ExitCode.USAGE
    # Act
    with pytest.raises(CliError) as raised:
        resolve_range(selection, now=NOW)
    # Assert
    assert raised.value.exit_code == expected


def test_flatten_groups_emits_one_row_per_node_with_its_level() -> None:
    # Arrange
    rows = [
        ReportGroupRow.model_validate({
            "_id": "u1",
            "name": "Ada",
            "duration": 90,
            "children": [{"_id": "p1", "name": "Web", "duration": 90}],
        })
    ]
    # Act
    flat = flatten_groups(rows)
    # Assert
    assert flat == [
        {"level": 1, "id": "u1", "name": "Ada", "duration": 90},
        {"level": 2, "id": "p1", "name": "Web", "duration": 90},
    ]


def test_describe_totals_formats_the_first_entry() -> None:
    # Arrange
    # Arrange
    totals = [ReportTotals(total_time=3600, total_billable_time=1800, entries_count=4)]
    # Act
    text = describe_totals(totals)
    # Assert
    assert text == "Total: 3600s (1800s billable) in 4 entries."


def test_describe_totals_is_empty_without_totals() -> None:
    # Arrange
    totals = None
    # Act
    text = describe_totals(totals)
    # Assert
    assert text is None
