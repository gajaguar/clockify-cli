from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from clockify import TimeOffAccrualPeriod
from clockify import TimeOffAutomaticAccrualRequest
from clockify import TimeOffAutomaticTimeEntryCreationRequest
from clockify import TimeOffDefaultEntitiesRequest
from clockify import TimeOffMemberFilterContains
from clockify import TimeOffNegativeBalanceRequest
from clockify import TimeOffPolicyApproval
from clockify import TimeOffPolicyMemberFilter
from clockify import TimeOffPolicyUpdate
from clockify import UserId

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.resolve import resolve_policy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from clockify import TimeOffPolicy
    from clockify import TimeOffPolicyIcon

    from clockify_unofficial_cli.runtime.context import AppContext


def member_filter(ids: Sequence[str]) -> TimeOffPolicyMemberFilter | None:
    if not ids:
        return None
    return TimeOffPolicyMemberFilter(ids=list(ids), contains=TimeOffMemberFilterContains.CONTAINS)


def approval(*, requires_approval: bool, approvers: Sequence[str], team_managers: bool) -> TimeOffPolicyApproval:
    return TimeOffPolicyApproval(
        requires_approval=requires_approval,
        specific_members=bool(approvers),
        team_managers=team_managers,
        user_ids=[UserId(approver) for approver in approvers],
    )


# What `time-off policy update` may change; None keeps the stored value.
@dataclass(frozen=True, slots=True)
class PolicyChanges:
    name: str | None = None
    color: str | None = None
    icon: TimeOffPolicyIcon | None = None
    allow_half_day: bool | None = None
    allow_negative_balance: bool | None = None
    everyone_including_new: bool | None = None
    requires_approval: bool | None = None
    users: Sequence[str] = ()
    groups: Sequence[str] = ()


def _flag(changed: bool | None, current: bool | None) -> bool:  # ruff: ignore[boolean-type-hint-positional-argument]  mirrors a tri-state CLI flag
    return changed if changed is not None else bool(current)


def _carried_period(period: str | None) -> TimeOffAccrualPeriod | None:
    return TimeOffAccrualPeriod(period) if period in {"MONTH", "YEAR"} else None


# Clockify's PUT replaces the whole policy, so anything the caller leaves alone has to be copied from
# the stored one or it would be wiped: accrual, negative balance, automatic entries and members.
def build_policy_update(current: TimeOffPolicy, changes: PolicyChanges) -> TimeOffPolicyUpdate:
    stored_approval = current.approve or TimeOffPolicyApproval()
    carried_users = current.user_ids or []
    carried_groups = current.user_group_ids or []
    fields: dict[str, object] = {
        "name": changes.name if changes.name is not None else current.name or "",
        "approve": TimeOffPolicyApproval(
            requires_approval=_flag(changes.requires_approval, stored_approval.requires_approval),
            specific_members=stored_approval.specific_members,
            team_managers=stored_approval.team_managers,
            user_ids=stored_approval.user_ids,
        ),
        "allow_half_day": _flag(changes.allow_half_day, current.allow_half_day),
        "allow_negative_balance": _flag(changes.allow_negative_balance, current.allow_negative_balance),
        "archived": bool(current.archived),
        "everyone_including_new": _flag(changes.everyone_including_new, current.everyone_including_new),
        "has_expiration": bool((current.model_extra or {}).get("hasExpiration")),
        "color": changes.color if changes.color is not None else current.color,
        "icon": changes.icon if changes.icon is not None else current.icon,
        "users": member_filter(changes.users or [str(user) for user in carried_users]),
        "user_groups": member_filter(changes.groups or [str(group) for group in carried_groups]),
    }
    accrual = current.automatic_accrual
    if accrual is not None and accrual.amount is not None:
        fields["automatic_accrual"] = TimeOffAutomaticAccrualRequest(amount=accrual.amount, period=accrual.period)
    negative = current.negative_balance
    if negative is not None and negative.amount is not None:
        fields["negative_balance"] = TimeOffNegativeBalanceRequest(
            amount=negative.amount, period=_carried_period(negative.period), should_reset=negative.should_reset
        )
    creation = current.automatic_time_entry_creation
    if creation is not None and creation.default_entities is not None:
        entities = creation.default_entities
        fields["automatic_time_entry_creation"] = TimeOffAutomaticTimeEntryCreationRequest(
            default_entities=TimeOffDefaultEntitiesRequest(project_id=entities.project_id, task_id=entities.task_id),
            enabled=creation.enabled,
        )
    return TimeOffPolicyUpdate(**{key: value for key, value in fields.items() if value is not None})  # type: ignore[arg-type]


# Clockify has no endpoint that reads one request, but every request route hangs off its policy.
# Without --policy the id is looked up in the workspace list to learn which policy it belongs to.
def policy_of_request(app_context: AppContext, request_id: str, policy_term: str | None) -> str:
    if policy_term is not None:
        return resolve_policy(app_context, policy_term)
    for found in app_context.workspace().time_off_requests.list():
        if str(found.id) == request_id and found.policy_id is not None:
            return str(found.policy_id)
    message = f"Time off request '{request_id}' not found; pass --policy if it is not listed."
    raise CliError(message, exit_code=ExitCode.NOT_FOUND)


__all__ = ["PolicyChanges", "approval", "build_policy_update", "member_filter", "policy_of_request"]
