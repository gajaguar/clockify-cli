import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ApprovalSortOrder
from clockify import TimeOffAccrualPeriod
from clockify import TimeOffAutomaticAccrualRequest
from clockify import TimeOffPolicyCreate
from clockify import TimeOffPolicyFilter
from clockify import TimeOffPolicyIcon
from clockify import TimeOffPolicyStatus
from clockify import TimeOffPolicyStatusUpdate
from clockify import TimeOffUnit

from clockify_unofficial_cli.output.columns import TIME_OFF_POLICIES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.resolve import resolve_group
from clockify_unofficial_cli.services.resolve import resolve_policy
from clockify_unofficial_cli.services.resolve import resolve_user
from clockify_unofficial_cli.services.time_off import PolicyChanges
from clockify_unofficial_cli.services.time_off import approval
from clockify_unofficial_cli.services.time_off import build_policy_update
from clockify_unofficial_cli.services.time_off import member_filter

APP: Final = typer.Typer(help="Manage time off policies.", no_args_is_help=True)

_POLICY_ARGUMENT: Final = typer.Argument(metavar="POLICY", help="Policy ID or exact name.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    name: Annotated[str | None, typer.Option("--name", help="Only policies whose name matches.")] = None
    status: Annotated[
        TimeOffPolicyStatus | None,
        typer.Option("--status", case_sensitive=False, help="ACTIVE, ARCHIVED or ALL."),
    ] = None
    sort_column: Annotated[str | None, typer.Option("--sort-column", help="Column to sort by.")] = None
    sort_order: Annotated[
        ApprovalSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


@APP.command(name="list", help="List the workspace's time off policies.")
@handle_errors
@options_from(_ListOptions)
def list_policies(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    policies = app_context.workspace().time_off_policies
    policy_filter = TimeOffPolicyFilter(
        name=options.name, status=options.status, sort_column=options.sort_column, sort_order=options.sort_order
    )
    found = list_from_options(
        functools.partial(policies.list, policy_filter=policy_filter),
        functools.partial(policies.list_page, policy_filter=policy_filter),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, TIME_OFF_POLICIES))


@APP.command(help="Show a policy by ID or exact name.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, _POLICY_ARGUMENT]) -> None:
    app_context = get_app_context(ctx)
    policy = app_context.workspace().time_off_policies.get(resolve_policy(app_context, term))
    app_context.render(single(policy, TIME_OFF_POLICIES))


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    name: Annotated[str, typer.Option("--name", help="Policy name.")]
    unit: Annotated[
        TimeOffUnit | None,
        typer.Option("--unit", case_sensitive=False, help="DAYS or HOURS; cannot change later."),
    ] = None
    requires_approval: Annotated[
        bool,
        typer.Option("--requires-approval/--no-approval", help="Whether requests wait for an approver."),
    ] = False
    approvers: Annotated[
        list[str] | None,
        typer.Option("--approver", help="User ID, email or name allowed to approve; repeatable."),
    ] = None
    team_managers: Annotated[bool, typer.Option("--team-managers", help="Team managers can approve.")] = False
    allow_half_day: Annotated[bool, typer.Option("--allow-half-day", help="Allow half-day requests.")] = False
    allow_negative_balance: Annotated[
        bool,
        typer.Option("--allow-negative-balance", help="Let the balance go below zero."),
    ] = False
    everyone: Annotated[
        bool,
        typer.Option("--everyone", help="Apply to every member, including those who join later."),
    ] = False
    users: Annotated[list[str] | None, typer.Option("--user", help="Member the policy applies to; repeatable.")] = None
    groups: Annotated[list[str] | None, typer.Option("--group", help="Group the policy applies to; repeatable.")] = (
        None
    )
    color: Annotated[str | None, typer.Option("--color", help="Hex color, e.g. #0f62fe.")] = None
    icon: Annotated[TimeOffPolicyIcon | None, typer.Option("--icon", case_sensitive=False, help="Icon.")] = None
    accrual_amount: Annotated[float | None, typer.Option("--accrual-amount", help="Amount accrued per period.")] = None
    accrual_period: Annotated[
        TimeOffAccrualPeriod | None,
        typer.Option("--accrual-period", case_sensitive=False, help="MONTH or YEAR."),
    ] = None


def _user_ids(app_context: AppContext, terms: list[str] | None) -> list[str]:
    return [resolve_user(app_context, term) for term in terms or []]


def _group_ids(app_context: AppContext, terms: list[str] | None) -> list[str]:
    return [resolve_group(app_context, term) for term in terms or []]


@APP.command(help="Create a time off policy.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    optional: dict[str, object] = {
        "time_unit": options.unit,
        "color": options.color,
        "icon": options.icon,
        "users": member_filter(_user_ids(app_context, options.users)),
        "user_groups": member_filter(_group_ids(app_context, options.groups)),
    }
    if options.accrual_amount is not None:
        optional["automatic_accrual"] = TimeOffAutomaticAccrualRequest(
            amount=options.accrual_amount, period=options.accrual_period
        )
    payload = TimeOffPolicyCreate(
        name=options.name,
        approve=approval(
            requires_approval=options.requires_approval,
            approvers=_user_ids(app_context, options.approvers),
            team_managers=options.team_managers,
        ),
        allow_half_day=options.allow_half_day,
        allow_negative_balance=options.allow_negative_balance,
        everyone_including_new=options.everyone,
        **{key: value for key, value in optional.items() if value is not None},  # type: ignore[arg-type]
    )
    policy = app_context.workspace().time_off_policies.create(payload)
    app_context.render(single(policy, TIME_OFF_POLICIES))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    term: Annotated[str, _POLICY_ARGUMENT]
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None
    color: Annotated[str | None, typer.Option("--color", help="New hex color.")] = None
    icon: Annotated[TimeOffPolicyIcon | None, typer.Option("--icon", case_sensitive=False, help="New icon.")] = None
    requires_approval: Annotated[
        bool | None,
        typer.Option("--requires-approval/--no-approval", help="Whether requests wait for an approver."),
    ] = None
    allow_half_day: Annotated[
        bool | None,
        typer.Option("--allow-half-day/--no-half-day", help="Allow or forbid half-day requests."),
    ] = None
    allow_negative_balance: Annotated[
        bool | None,
        typer.Option("--allow-negative-balance/--no-negative-balance", help="Allow or forbid a negative balance."),
    ] = None
    everyone: Annotated[
        bool | None,
        typer.Option("--everyone/--no-everyone", help="Apply to every member, including later ones."),
    ] = None
    users: Annotated[list[str] | None, typer.Option("--user", help="Replace the members; repeatable.")] = None
    groups: Annotated[list[str] | None, typer.Option("--group", help="Replace the groups; repeatable.")] = None


# Clockify's PUT wants every field, so the service copies whatever these options leave out.
@APP.command(help="Update a policy; options left out keep their current value.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    policies = app_context.workspace().time_off_policies
    policy_id = resolve_policy(app_context, options.term)
    changes = PolicyChanges(
        name=options.name,
        color=options.color,
        icon=options.icon,
        allow_half_day=options.allow_half_day,
        allow_negative_balance=options.allow_negative_balance,
        everyone_including_new=options.everyone,
        requires_approval=options.requires_approval,
        users=_user_ids(app_context, options.users),
        groups=_group_ids(app_context, options.groups),
    )
    payload = build_policy_update(policies.get(policy_id), changes)
    app_context.render(single(policies.update(policy_id, payload), TIME_OFF_POLICIES))


def _set_status(ctx: typer.Context, term: str, status: TimeOffPolicyStatus) -> None:
    app_context = get_app_context(ctx)
    policies = app_context.workspace().time_off_policies
    policy = policies.update_status(resolve_policy(app_context, term), TimeOffPolicyStatusUpdate(status=status))
    app_context.render(single(policy, TIME_OFF_POLICIES))


@APP.command(help="Archive a policy.")
@handle_errors
def archive(ctx: typer.Context, term: Annotated[str, _POLICY_ARGUMENT]) -> None:
    _set_status(ctx, term, TimeOffPolicyStatus.ARCHIVED)


@APP.command(help="Restore an archived policy.")
@handle_errors
def restore(ctx: typer.Context, term: Annotated[str, _POLICY_ARGUMENT]) -> None:
    _set_status(ctx, term, TimeOffPolicyStatus.ACTIVE)


@APP.command(help="Delete a policy.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, _POLICY_ARGUMENT],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete time off policy '{term}'", assume_yes=yes)
    policy_id = resolve_policy(app_context, term)
    app_context.workspace().time_off_policies.delete(policy_id)
    app_context.notify(f"Deleted time off policy '{policy_id}'.")
