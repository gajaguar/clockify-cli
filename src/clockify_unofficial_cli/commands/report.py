from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import DetailedFilter
from clockify import DetailedReportRequest
from clockify import ReportGroup
from clockify import ReportSortOrder
from clockify import SummaryFilter
from clockify import SummaryReportRequest
from clockify import WeeklyFilter
from clockify import WeeklyReportRequest
from clockify import WeeklySubgroup

from clockify_unofficial_cli.output.columns import REPORT_ENTRIES
from clockify_unofficial_cli.output.columns import REPORT_GROUPS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.services.reports import Period
from clockify_unofficial_cli.services.reports import ReportQuery
from clockify_unofficial_cli.services.reports import ReportSelection
from clockify_unofficial_cli.services.reports import build_query
from clockify_unofficial_cli.services.reports import describe_totals
from clockify_unofficial_cli.services.reports import flatten_groups

APP: Final = typer.Typer(
    help="Summarize tracked time. Rows go to stdout; the totals line goes to stderr.", no_args_is_help=True
)


@dataclass(frozen=True, slots=True)
class _CommonOptions:
    period: Annotated[
        Period | None,
        typer.Option("--period", help="Date range preset in local time; this-week when no range is given."),
    ] = None
    start: Annotated[str | None, typer.Option("--from", help="Range start, e.g. 2026-09-01 or 'yesterday 09:00'.")] = (
        None
    )
    end: Annotated[str | None, typer.Option("--to", help="Range end; defaults to now when only --from is given.")] = (
        None
    )
    projects: Annotated[list[str] | None, typer.Option("--project", "-P", help="Project ID or name; repeatable.")] = (
        None
    )
    clients: Annotated[list[str] | None, typer.Option("--client", help="Client ID or name; repeatable.")] = None
    tags: Annotated[list[str] | None, typer.Option("--tag", help="Tag ID or name; repeatable.")] = None
    users: Annotated[list[str] | None, typer.Option("--user", help="User ID, email or name; repeatable.")] = None
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--non-billable", help="Only billable or only non-billable entries."),
    ] = None
    description: Annotated[str | None, typer.Option("--description", help="Only entries whose text matches.")] = None
    time_zone: Annotated[str | None, typer.Option("--timezone", help="IANA time zone for grouping, e.g. UTC.")] = None
    sort_order: Annotated[
        ReportSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


def _query(app_context: AppContext, options: _CommonOptions) -> ReportQuery:
    selection = ReportSelection(
        period=options.period,
        start=options.start,
        end=options.end,
        projects=options.projects or (),
        clients=options.clients or (),
        tags=options.tags or (),
        users=options.users or (),
        billable=options.billable,
        description=options.description,
        time_zone=options.time_zone,
        sort_order=options.sort_order,
    )
    return build_query(app_context, selection)


@dataclass(frozen=True, slots=True)
class _SummaryOptions(_CommonOptions):
    group_by: Annotated[
        list[ReportGroup] | None,
        typer.Option("--group-by", case_sensitive=False, help="Grouping level, outermost first; default PROJECT."),
    ] = None
    sort_column: Annotated[str | None, typer.Option("--sort-column", help="Column to sort the groups by.")] = None


@APP.command(help="Total tracked time grouped by project, user, tag and more.")
@handle_errors
@options_from(_SummaryOptions)
def summary(ctx: typer.Context, options: _SummaryOptions) -> None:
    app_context = get_app_context(ctx)
    request = SummaryReportRequest(
        **_query(app_context, options).fields(),
        summary_filter=SummaryFilter(
            groups=options.group_by or [ReportGroup.PROJECT], sort_column=options.sort_column
        ),
    )
    report = app_context.workspace().reports.summary(request)
    _announce(app_context, describe_totals(report.totals))
    app_context.render(many(flatten_groups(report.group_one), REPORT_GROUPS))


@dataclass(frozen=True, slots=True)
class _DetailedOptions(_CommonOptions):
    page: Annotated[int, typer.Option("--page", min=1, help="1-based page number.")] = 1
    page_size: Annotated[int, typer.Option("--page-size", min=1, max=1000, help="Entries per page.")] = 50
    sort_column: Annotated[str | None, typer.Option("--sort-column", help="Column to sort the entries by.")] = None


@APP.command(help="Every time entry in the range, one row each.")
@handle_errors
@options_from(_DetailedOptions)
def detailed(ctx: typer.Context, options: _DetailedOptions) -> None:
    app_context = get_app_context(ctx)
    request = DetailedReportRequest(
        **_query(app_context, options).fields(),
        detailed_filter=DetailedFilter(
            page=options.page, page_size=options.page_size, sort_column=options.sort_column
        ),
    )
    report = app_context.workspace().reports.detailed(request)
    _announce(app_context, describe_totals(report.totals))
    app_context.render(many(report.time_entries, REPORT_ENTRIES))


@dataclass(frozen=True, slots=True)
class _WeeklyOptions(_CommonOptions):
    group: Annotated[
        ReportGroup,
        typer.Option("--group", case_sensitive=False, help="What each row is grouped by."),
    ] = ReportGroup.USER
    subgroup: Annotated[
        WeeklySubgroup | None,
        typer.Option("--subgroup", case_sensitive=False, help="TIME or EARNINGS."),
    ] = None


@APP.command(help="Tracked time per week day.")
@handle_errors
@options_from(_WeeklyOptions)
def weekly(ctx: typer.Context, options: _WeeklyOptions) -> None:
    app_context = get_app_context(ctx)
    request = WeeklyReportRequest(
        **_query(app_context, options).fields(),
        weekly_filter=WeeklyFilter(group=options.group, subgroup=options.subgroup),
    )
    report = app_context.workspace().reports.weekly(request)
    _announce(app_context, describe_totals(report.totals))
    app_context.render(many(flatten_groups(report.group_one), REPORT_GROUPS))


def _announce(app_context: AppContext, totals: str | None) -> None:
    if totals is not None:
        app_context.notify(totals)
