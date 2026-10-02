import datetime
import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import TimeOffHalfDayPeriod
from clockify import TimeOffPeriodRequest
from clockify import TimeOffRequestCreate
from clockify import TimeOffRequestDecision
from clockify import TimeOffRequestFilter
from clockify import TimeOffRequestPeriodRequest
from clockify import TimeOffRequestStatusType
from clockify import TimeOffRequestStatusUpdate
from clockify import UserGroupId
from clockify import UserId

from clockify_unofficial_cli.output.columns import TIME_OFF_REQUESTS
from clockify_unofficial_cli.output.columns import TIME_OFF_REQUEST_RESULT
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.parsing import parse_date
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_group
from clockify_unofficial_cli.services.resolve import resolve_policy
from clockify_unofficial_cli.services.resolve import resolve_user
from clockify_unofficial_cli.services.time_off import policy_of_request

APP: Final = typer.Typer(help="List, create and decide time off requests.", no_args_is_help=True)

_REQUEST_ARGUMENT: Final = typer.Argument(metavar="REQUEST", help="Time off request ID.")
_POLICY_OPTION: Final = typer.Option(
    "--policy", "-P", help="Policy ID or name; looked up from the request when left out."
)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    statuses: Annotated[
        list[TimeOffRequestStatusType] | None,
        typer.Option("--status", case_sensitive=False, help="PENDING, APPROVED, REJECTED or ALL; repeatable."),
    ] = None
    users: Annotated[list[str] | None, typer.Option("--user", help="Requester ID, email or name; repeatable.")] = None
    groups: Annotated[list[str] | None, typer.Option("--group", help="Requester group; repeatable.")] = None
    start: Annotated[str | None, typer.Option("--from", help="Only requests from this instant.")] = None
    end: Annotated[str | None, typer.Option("--to", help="Only requests up to this instant.")] = None


@APP.command(name="list", help="List time off requests in the workspace.")
@handle_errors
@options_from(_ListOptions)
def list_requests(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.workspace().time_off_requests
    request_filter = TimeOffRequestFilter(
        start=parse_instant(options.start) if options.start else None,
        end=parse_instant(options.end) if options.end else None,
        statuses=options.statuses,
        users=[UserId(resolve_user(app_context, term)) for term in options.users] if options.users else None,
        user_groups=[UserGroupId(resolve_group(app_context, term)) for term in options.groups]
        if options.groups
        else None,
    )
    found = list_from_options(
        functools.partial(requests.list, request_filter=request_filter),
        functools.partial(requests.list_page, request_filter=request_filter),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, TIME_OFF_REQUESTS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    policy: Annotated[str, typer.Option("--policy", "-P", help="Policy ID or name.")]
    start: Annotated[str, typer.Option("--from", help="First day, e.g. 2026-09-14 or tomorrow.")]
    end: Annotated[str | None, typer.Option("--to", help="Last day; defaults to --from.")] = None
    half_day: Annotated[
        TimeOffHalfDayPeriod | None,
        typer.Option("--half-day", case_sensitive=False, help="FIRST_HALF or SECOND_HALF; one day only."),
    ] = None
    note: Annotated[str | None, typer.Option("--note", help="Note for the approver.")] = None
    user: Annotated[str | None, typer.Option("--user", help="Request on behalf of this user.")] = None


def _period(
    start: datetime.date, end: datetime.date | None, half_day: TimeOffHalfDayPeriod | None
) -> TimeOffRequestPeriodRequest:
    period = TimeOffPeriodRequest(start=start, end=end or start)
    if half_day is None:
        return TimeOffRequestPeriodRequest(period=period)
    return TimeOffRequestPeriodRequest(period=period, is_half_day=True, half_day_period=half_day)


@APP.command(help="Request time off, optionally on behalf of another user.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.workspace().time_off_requests
    policy_id = resolve_policy(app_context, options.policy)
    fields: dict[str, object] = {"note": options.note} if options.note is not None else {}
    payload = TimeOffRequestCreate(
        time_off_period=_period(
            parse_date(options.start), parse_date(options.end) if options.end else None, options.half_day
        ),
        **fields,  # type: ignore[arg-type]
    )
    if options.user is None:
        created = requests.create(policy_id, payload)
    else:
        created = requests.create_for_user(policy_id, resolve_user(app_context, options.user), payload)
    app_context.render(single(created, TIME_OFF_REQUESTS))


def _decide(
    ctx: typer.Context, request_id: str, policy_term: str | None, decision: TimeOffRequestDecision, note: str | None
) -> None:
    app_context = get_app_context(ctx)
    policy_id = policy_of_request(app_context, request_id, policy_term)
    fields: dict[str, object] = {"note": note} if note is not None else {}
    payload = TimeOffRequestStatusUpdate(status=decision, **fields)  # type: ignore[arg-type]
    decided = app_context.workspace().time_off_requests.update_status(policy_id, request_id, payload)
    app_context.render(single(decided, TIME_OFF_REQUEST_RESULT))


@APP.command(help="Approve a time off request.")
@handle_errors
def approve(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    policy: Annotated[str | None, _POLICY_OPTION] = None,
    note: Annotated[str | None, typer.Option("--note", help="Note for the requester.")] = None,
) -> None:
    _decide(ctx, request_id, policy, TimeOffRequestDecision.APPROVED, note)


@APP.command(help="Reject a time off request.")
@handle_errors
def reject(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    policy: Annotated[str | None, _POLICY_OPTION] = None,
    note: Annotated[str | None, typer.Option("--note", help="Note for the requester.")] = None,
) -> None:
    _decide(ctx, request_id, policy, TimeOffRequestDecision.REJECTED, note)


@APP.command(help="Delete a time off request.")
@handle_errors
def delete(
    ctx: typer.Context,
    request_id: Annotated[str, _REQUEST_ARGUMENT],
    *,
    policy: Annotated[str | None, _POLICY_OPTION] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete time off request '{request_id}'", assume_yes=yes)
    policy_id = policy_of_request(app_context, request_id, policy)
    app_context.workspace().time_off_requests.delete(policy_id, request_id)
    app_context.notify(f"Deleted time off request '{request_id}'.")
