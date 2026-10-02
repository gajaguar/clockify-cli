from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

from clockify import ReportEntityFilter
from clockify import ReportFilterContains

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_client
from clockify_unofficial_cli.services.resolve import resolve_project
from clockify_unofficial_cli.services.resolve import resolve_tag
from clockify_unofficial_cli.services.resolve import resolve_user

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Sequence

    from clockify import ReportGroupRow
    from clockify import ReportSortOrder
    from clockify import ReportTotals

    from clockify_unofficial_cli.output.renderer import Record
    from clockify_unofficial_cli.runtime.context import AppContext


class Period(StrEnum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this-week"
    LAST_WEEK = "last-week"
    THIS_MONTH = "this-month"
    LAST_MONTH = "last-month"


@dataclass(frozen=True, slots=True)
class DateRange:
    start: datetime.datetime
    end: datetime.datetime


@dataclass(frozen=True, slots=True)
class ReportSelection:
    period: Period | None = None
    start: str | None = None
    end: str | None = None
    projects: Sequence[str] = ()
    clients: Sequence[str] = ()
    tags: Sequence[str] = ()
    users: Sequence[str] = ()
    billable: bool | None = None
    description: str | None = None
    time_zone: str | None = None
    sort_order: ReportSortOrder | None = None


# The fields every report request shares; each command adds its own filter on top.
@dataclass(frozen=True, slots=True)
class ReportQuery:
    date_range: DateRange
    filters: dict[str, ReportEntityFilter]
    billable: bool | None
    description: str | None
    time_zone: str | None
    sort_order: ReportSortOrder | None

    def fields(self) -> dict[str, Any]:
        return {
            "date_range_start": self.date_range.start,
            "date_range_end": self.date_range.end,
            "billable": self.billable,
            "description": self.description,
            "time_zone": self.time_zone,
            "sort_order": self.sort_order,
            **self.filters,
        }


_ONE_SECOND: Final = datetime.timedelta(seconds=1)


def _start_of_day(moment: datetime.datetime) -> datetime.datetime:
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month(moment: datetime.datetime) -> datetime.datetime:
    return _start_of_day(moment).replace(day=1)


def _next_month(first_of_month: datetime.datetime) -> datetime.datetime:
    return (first_of_month + datetime.timedelta(days=32)).replace(day=1)


# The upper bound is the last second of the period, because Clockify treats dateRangeEnd as inclusive.
def _preset(period: Period, now: datetime.datetime) -> DateRange:
    today = _start_of_day(now)
    monday = today - datetime.timedelta(days=today.weekday())
    month = _start_of_month(now)
    bounds: dict[Period, tuple[datetime.datetime, datetime.datetime]] = {
        Period.TODAY: (today, today + datetime.timedelta(days=1)),
        Period.YESTERDAY: (today - datetime.timedelta(days=1), today),
        Period.THIS_WEEK: (monday, monday + datetime.timedelta(days=7)),
        Period.LAST_WEEK: (monday - datetime.timedelta(days=7), monday),
        Period.THIS_MONTH: (month, _next_month(month)),
        Period.LAST_MONTH: (_start_of_month(month - datetime.timedelta(days=1)), month),
    }
    start, end = bounds[period]
    return DateRange(start=start.astimezone(datetime.UTC), end=(end - _ONE_SECOND).astimezone(datetime.UTC))


def resolve_range(selection: ReportSelection, *, now: datetime.datetime | None = None) -> DateRange:
    local_now = now or datetime.datetime.now().astimezone()
    explicit = selection.start is not None or selection.end is not None
    if selection.period is not None and explicit:
        message = "--period cannot be combined with --from/--to."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if not explicit:
        return _preset(selection.period or Period.THIS_WEEK, local_now)
    if selection.start is None:
        message = "--to needs --from."
        raise CliError(message, exit_code=ExitCode.USAGE)
    start = parse_instant(selection.start)
    end = parse_instant(selection.end) if selection.end is not None else local_now.astimezone(datetime.UTC)
    if end <= start:
        message = "--to must be after --from."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return DateRange(start=start, end=end)


def _entity_filter(
    app_context: AppContext, terms: Sequence[str], resolver: Callable[[AppContext, str], str]
) -> ReportEntityFilter | None:
    if not terms:
        return None
    ids = [resolver(app_context, term) for term in terms]
    return ReportEntityFilter(ids=ids, contains=ReportFilterContains.CONTAINS)


def build_query(
    app_context: AppContext, selection: ReportSelection, *, now: datetime.datetime | None = None
) -> ReportQuery:
    date_range = resolve_range(selection, now=now)
    candidates = {
        "projects": _entity_filter(app_context, selection.projects, resolve_project),
        "clients": _entity_filter(app_context, selection.clients, resolve_client),
        "tags": _entity_filter(app_context, selection.tags, resolve_tag),
        "users": _entity_filter(app_context, selection.users, resolve_user),
    }
    return ReportQuery(
        date_range=date_range,
        filters={name: found for name, found in candidates.items() if found is not None},
        billable=selection.billable,
        description=selection.description,
        time_zone=selection.time_zone,
        sort_order=selection.sort_order,
    )


# Group rows nest (user > project > ...); one flat row per node keeps table, CSV and JSON output
# uniform, and `level` preserves the hierarchy for anyone who needs to rebuild it.
def flatten_groups(rows: Iterable[ReportGroupRow] | None, level: int = 1) -> list[Record]:
    flat: list[Record] = []
    for row in rows or ():
        flat.append({"level": level, "id": row.id, "name": row.name, "duration": row.duration})
        flat.extend(flatten_groups(row.children, level + 1))
    return flat


def describe_totals(totals: Sequence[ReportTotals] | None) -> str | None:
    if not totals:
        return None
    first = totals[0]
    total, billable, count = first.total_time or 0, first.total_billable_time or 0, first.entries_count or 0
    return f"Total: {total}s ({billable}s billable) in {count} entries."


__all__ = [
    "DateRange",
    "Period",
    "ReportQuery",
    "ReportSelection",
    "build_query",
    "describe_totals",
    "flatten_groups",
    "resolve_range",
]
