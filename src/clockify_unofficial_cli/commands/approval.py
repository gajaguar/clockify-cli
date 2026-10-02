import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ApprovalPeriod
from clockify import ApprovalRequestCreate
from clockify import ApprovalRequestFilter
from clockify import ApprovalRequestResubmit
from clockify import ApprovalRequestType
from clockify import ApprovalRequestUpdate
from clockify import ApprovalSortColumn
from clockify import ApprovalSortOrder
from clockify import ApprovalState

from clockify_unofficial_cli.output.columns import APPROVALS
from clockify_unofficial_cli.output.columns import APPROVAL_REQUESTS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_user

APP: Final = typer.Typer(help="Submit and decide timesheet and expense approvals.", no_args_is_help=True)

_REQUEST_ARGUMENT: Final = typer.Argument(metavar="REQUEST", help="Approval request ID.")
_NOTE_OPTION: Final = typer.Option("--note", help="Note recorded with the decision.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    status: Annotated[
        ApprovalState | None,
        typer.Option("--status", case_sensitive=False, help="PENDING, APPROVED, REJECTED, ..."),
    ] = None
    types: Annotated[
        list[ApprovalRequestType] | None,
        typer.Option("--type", case_sensitive=False, help="TIMESHEET, EXPENSE or TIMESHEET_AND_EXPENSE; repeatable."),
    ] = None
    sort_column: Annotated[
        ApprovalSortColumn | None,
        typer.Option("--sort-column", case_sensitive=False, help="ID, USER_ID, START or UPDATED_AT."),
    ] = None
    sort_order: Annotated[
        ApprovalSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


@APP.command(name="list", help="List approval requests.")
@handle_errors
@options_from(_ListOptions)
def list_approvals(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    approvals = app_context.workspace().approvals
    request_filter = ApprovalRequestFilter(
        status=options.status, sort_column=options.sort_column, sort_order=options.sort_order, types=options.types
    )
    found = list_from_options(
        functools.partial(approvals.list, request_filter=request_filter),
        functools.partial(approvals.list_page, request_filter=request_filter),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, APPROVALS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _SubmitOptions:
    start: Annotated[str, typer.Option("--start", help="First day of the period, e.g. 2026-09-14.")]
    approval_type: Annotated[
        ApprovalRequestType,
        typer.Option("--type", case_sensitive=False, help="What to submit."),
    ] = ApprovalRequestType.TIMESHEET
    period: Annotated[
        ApprovalPeriod | None,
        typer.Option("--period", case_sensitive=False, help="WEEKLY, SEMI_MONTHLY or MONTHLY."),
    ] = None
    user: Annotated[str | None, typer.Option("--user", help="Submit on behalf of this user.")] = None


@APP.command(help="Submit a period for approval, optionally on behalf of a user.")
@handle_errors
@options_from(_SubmitOptions)
def submit(ctx: typer.Context, options: _SubmitOptions) -> None:
    app_context = get_app_context(ctx)
    approvals = app_context.workspace().approvals
    fields: dict[str, object] = {"period": options.period} if options.period is not None else {}
    payload = ApprovalRequestCreate(period_start=parse_instant(options.start), **fields)  # type: ignore[arg-type]
    if options.user is None:
        submitted = approvals.submit(options.approval_type, payload)
    else:
        submitted = approvals.submit_for_user(resolve_user(app_context, options.user), options.approval_type, payload)
    app_context.render(single(submitted, APPROVAL_REQUESTS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _ResubmitOptions:
    start: Annotated[str, typer.Option("--start", help="First day of the period, e.g. 2026-09-14.")]
    approval_type: Annotated[
        ApprovalRequestType | None,
        typer.Option("--type", case_sensitive=False, help="What to resubmit."),
    ] = None
    period: Annotated[
        ApprovalPeriod | None,
        typer.Option("--period", case_sensitive=False, help="WEEKLY, SEMI_MONTHLY or MONTHLY."),
    ] = None


@APP.command(help="Resubmit the entries of a rejected or withdrawn period.")
@handle_errors
@options_from(_ResubmitOptions)
def resubmit(ctx: typer.Context, options: _ResubmitOptions) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    if options.period is not None:
        fields["period"] = options.period
    if options.approval_type is not None:
        fields["type"] = options.approval_type
    payload = ApprovalRequestResubmit(period_start=parse_instant(options.start), **fields)  # type: ignore[arg-type]
    resubmitted = app_context.workspace().approvals.resubmit(payload)
    app_context.render(single(resubmitted, APPROVAL_REQUESTS))


def _decide(ctx: typer.Context, request_id: str, state: ApprovalState, note: str | None) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {"note": note} if note is not None else {}
    payload = ApprovalRequestUpdate(state=state, **fields)  # type: ignore[arg-type]
    decided = app_context.workspace().approvals.update(request_id, payload)
    app_context.render(single(decided, APPROVAL_REQUESTS))


@APP.command(help="Approve an approval request.")
@handle_errors
def approve(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    note: Annotated[str | None, _NOTE_OPTION] = None,
) -> None:
    _decide(ctx, request_id, ApprovalState.APPROVED, note)


@APP.command(help="Reject an approval request.")
@handle_errors
def reject(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    note: Annotated[str | None, _NOTE_OPTION] = None,
) -> None:
    _decide(ctx, request_id, ApprovalState.REJECTED, note)


@APP.command(help="Withdraw a submission, or with --approval an earlier approval.")
@handle_errors
def withdraw(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    approval: Annotated[
        bool,
        typer.Option("--approval", help="Withdraw an approval you gave instead of your own submission."),
    ] = False,
    note: Annotated[str | None, _NOTE_OPTION] = None,
) -> None:
    state = ApprovalState.WITHDRAWN_APPROVAL if approval else ApprovalState.WITHDRAWN_SUBMISSION
    _decide(ctx, request_id, state, note)
