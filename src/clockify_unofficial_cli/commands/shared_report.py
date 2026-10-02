from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ReportSortOrder
from clockify import SharedReportQuery

from clockify_unofficial_cli.output.renderer import Column
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.output.renderer import to_record
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.services.parsing import parse_instant

APP: Final = typer.Typer(help="Open reports shared from the Clockify web app.", no_args_is_help=True)


@dataclass(frozen=True, slots=True)
class _GenerateOptions:
    report_id: Annotated[str, typer.Argument(metavar="REPORT", help="Shared report ID.")]
    start: Annotated[str | None, typer.Option("--from", help="Override the range start.")] = None
    end: Annotated[str | None, typer.Option("--to", help="Override the range end.")] = None
    sort_order: Annotated[
        ReportSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None
    sort_column: Annotated[str | None, typer.Option("--sort-column", help="Column to sort by.")] = None
    page: Annotated[int | None, typer.Option("--page", min=1, help="1-based page number.")] = None
    page_size: Annotated[int | None, typer.Option("--page-size", min=1, help="Entries per page.")] = None


# The payload's shape depends on the kind of report that was shared, so the columns follow its keys.
@APP.command(help="Fetch the data of a shared report by its ID.")
@handle_errors
@options_from(_GenerateOptions)
def generate(ctx: typer.Context, options: _GenerateOptions) -> None:
    app_context = get_app_context(ctx)
    query = SharedReportQuery(
        date_range_start=parse_instant(options.start) if options.start else None,
        date_range_end=parse_instant(options.end) if options.end else None,
        sort_order=options.sort_order,
        sort_column=options.sort_column,
        page=options.page,
        page_size=options.page_size,
    )
    report = app_context.workspace().reports.shared(options.report_id, query=query)
    record = to_record(report)
    app_context.render(single(record, tuple(Column(key, key) for key in record)))
