import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ApprovalSortOrder
from clockify import TimeOffBalanceAssignmentCreate
from clockify import TimeOffBalanceAssignmentDelete
from clockify import TimeOffBalanceAssignmentUpdate
from clockify import TimeOffBalanceDateRange
from clockify import TimeOffBalanceFilter
from clockify import TimeOffBalanceSortColumn
from clockify import TimeOffBalanceUpdate
from clockify import TimeOffPolicyId
from clockify import UserId

from clockify_unofficial_cli.output.columns import TIME_OFF_ASSIGNMENTS
from clockify_unofficial_cli.output.columns import TIME_OFF_BALANCES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.parsing import parse_date
from clockify_unofficial_cli.services.resolve import resolve_policy
from clockify_unofficial_cli.services.resolve import resolve_user

APP: Final = typer.Typer(help="Read and change time off balances.", no_args_is_help=True)

_POLICY_OPTION: Final = typer.Option("--policy", "-P", help="Policy ID or name.")


def _date_range(start: str | None, end: str | None) -> TimeOffBalanceDateRange | None:
    bounds = {"start": start, "end": end}
    given = {name: parse_date(value) for name, value in bounds.items() if value is not None}
    return TimeOffBalanceDateRange(**given) if given else None


def _users(app_context: AppContext, terms: list[str]) -> list[UserId]:
    return [UserId(resolve_user(app_context, term)) for term in terms]


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    policy: Annotated[str | None, typer.Option("--policy", "-P", help="List the balances of this policy.")] = None
    user: Annotated[str | None, typer.Option("--user", help="List the balances of this user.")] = None
    sort_column: Annotated[
        TimeOffBalanceSortColumn | None,
        typer.Option("--sort-column", case_sensitive=False, help="USER, POLICY, USED, BALANCE or TOTAL."),
    ] = None
    sort_order: Annotated[
        ApprovalSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


@APP.command(name="list", help="List balances of one policy (-P) or of one user (--user).")
@handle_errors
@options_from(_ListOptions)
def list_balances(ctx: typer.Context, options: _ListOptions) -> None:
    if (options.policy is None) == (options.user is None):
        message = "Pass exactly one of --policy or --user."
        raise CliError(message, exit_code=ExitCode.USAGE)
    app_context = get_app_context(ctx)
    balances = app_context.workspace().time_off_balances
    balance_filter = TimeOffBalanceFilter(sort_column=options.sort_column, sort_order=options.sort_order)
    if options.policy is not None:
        policy_id = resolve_policy(app_context, options.policy)
        fetch_all = functools.partial(balances.list_for_policy, policy_id, balance_filter=balance_filter)
        fetch_page = functools.partial(balances.list_for_policy_page, policy_id, balance_filter=balance_filter)
    else:
        user_id = resolve_user(app_context, options.user or "")
        fetch_all = functools.partial(balances.list_for_user, user_id, balance_filter=balance_filter)
        fetch_page = functools.partial(balances.list_for_user_page, user_id, balance_filter=balance_filter)
    found = list_from_options(fetch_all, fetch_page, options.limit, options.page, options.page_size)
    app_context.render(many(found, TIME_OFF_BALANCES))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    policy: Annotated[str, _POLICY_OPTION]
    users: Annotated[list[str], typer.Option("--user", help="User ID, email or name; repeatable.")]
    value: Annotated[float, typer.Option("--value", help="Amount to add to the balance; negative subtracts.")]
    start: Annotated[str | None, typer.Option("--from", help="Start of the validity range.")] = None
    end: Annotated[str | None, typer.Option("--to", help="End of the validity range.")] = None
    note: Annotated[str | None, typer.Option("--note", help="Why the balance changes.")] = None
    sync: Annotated[bool, typer.Option("--sync", help="Also sync it to the users' assignments.")] = False


# `--value` is a delta and Clockify does not retry it, so repeating the command adds it twice.
@APP.command(help="Add to (or subtract from) the balance of users under a policy.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    date_range = _date_range(options.start, options.end)
    if date_range is not None:
        fields["date_range"] = date_range
    if options.note is not None:
        fields["note"] = options.note
    if options.sync:
        fields["sync"] = True
    payload = TimeOffBalanceUpdate(user_ids=_users(app_context, options.users), value=options.value, **fields)  # type: ignore[arg-type]
    app_context.workspace().time_off_balances.update(resolve_policy(app_context, options.policy), payload)
    app_context.notify(f"Changed the balance by {options.value}.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _AssignOptions:
    policy: Annotated[str, _POLICY_OPTION]
    users: Annotated[list[str], typer.Option("--user", help="User ID, email or name; repeatable.")]
    balance: Annotated[float, typer.Option("--balance", help="Balance to assign.")]
    start: Annotated[str | None, typer.Option("--from", help="Start of the validity range.")] = None
    end: Annotated[str | None, typer.Option("--to", help="End of the validity range.")] = None
    note: Annotated[str | None, typer.Option("--note", help="Why the balance is assigned.")] = None


@APP.command(help="Assign a balance to users under a policy.")
@handle_errors
@options_from(_AssignOptions)
def assign(ctx: typer.Context, options: _AssignOptions) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    date_range = _date_range(options.start, options.end)
    if date_range is not None:
        fields["date_range"] = date_range
    if options.note is not None:
        fields["note"] = options.note
    payload = TimeOffBalanceAssignmentCreate(
        policy_id=TimeOffPolicyId(resolve_policy(app_context, options.policy)),
        user_ids=_users(app_context, options.users),
        balance=options.balance,
        **fields,  # type: ignore[arg-type]
    )
    app_context.workspace().time_off_balances.create_assignment(payload)
    app_context.notify(f"Assigned a balance of {options.balance}.")


@APP.command(help="List the balance assignments of a user under a policy.")
@handle_errors
def assignments(
    ctx: typer.Context,
    *,
    policy: Annotated[str, _POLICY_OPTION],
    user: Annotated[str, typer.Option("--user", help="User ID, email or name.")],
) -> None:
    app_context = get_app_context(ctx)
    found = app_context.workspace().time_off_balances.list_assignments(
        resolve_user(app_context, user), resolve_policy(app_context, policy)
    )
    app_context.render(many(found, TIME_OFF_ASSIGNMENTS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateAssignmentOptions:
    assignment: Annotated[str, typer.Argument(metavar="ASSIGNMENT", help="Balance assignment ID.")]
    policy: Annotated[str, _POLICY_OPTION]
    user: Annotated[str, typer.Option("--user", help="User ID, email or name.")]
    change: Annotated[float, typer.Option("--change", help="Amount to add to the assignment; negative subtracts.")]
    start: Annotated[str | None, typer.Option("--from", help="New start of the validity range.")] = None
    end: Annotated[str | None, typer.Option("--to", help="New end of the validity range.")] = None
    note: Annotated[str | None, typer.Option("--note", help="Why the assignment changes.")] = None


@APP.command(name="update-assignment", help="Change the balance of an assignment by a delta.")
@handle_errors
@options_from(_UpdateAssignmentOptions)
def update_assignment(ctx: typer.Context, options: _UpdateAssignmentOptions) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    date_range = _date_range(options.start, options.end)
    if date_range is not None:
        fields["date_range"] = date_range
    if options.note is not None:
        fields["note"] = options.note
    payload = TimeOffBalanceAssignmentUpdate(balance_change=options.change, **fields)  # type: ignore[arg-type]
    app_context.workspace().time_off_balances.update_assignment(
        options.assignment,
        resolve_user(app_context, options.user),
        resolve_policy(app_context, options.policy),
        payload,
    )
    app_context.notify(f"Changed assignment '{options.assignment}' by {options.change}.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteAssignmentOptions:
    assignment: Annotated[str, typer.Argument(metavar="ASSIGNMENT", help="Balance assignment ID.")]
    policy: Annotated[str, _POLICY_OPTION]
    user: Annotated[str, typer.Option("--user", help="User ID, email or name.")]
    note: Annotated[str, typer.Option("--note", help="Why the assignment is deleted.")]
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False


@APP.command(name="delete-assignment", help="Delete a balance assignment; Clockify requires a note.")
@handle_errors
@options_from(_DeleteAssignmentOptions)
def delete_assignment(ctx: typer.Context, options: _DeleteAssignmentOptions) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete balance assignment '{options.assignment}'", assume_yes=options.yes)
    app_context.workspace().time_off_balances.delete_assignment(
        options.assignment,
        resolve_user(app_context, options.user),
        resolve_policy(app_context, options.policy),
        TimeOffBalanceAssignmentDelete(note=options.note),
    )
    app_context.notify(f"Deleted balance assignment '{options.assignment}'.")
