from __future__ import annotations

from typing import Final

from clockify import TimeOffPolicy
from clockify import TimeOffPolicyIcon

from clockify_unofficial_cli.services.time_off import PolicyChanges
from clockify_unofficial_cli.services.time_off import approval
from clockify_unofficial_cli.services.time_off import build_policy_update
from clockify_unofficial_cli.services.time_off import member_filter

STORED: Final = {
    "id": "888888888888888888888888",
    "name": "Vacation",
    "archived": True,
    "hasExpiration": True,
    "color": "#fff",
    "approve": {"requiresApproval": True, "specificMembers": True, "teamManagers": True, "userIds": ["u1"]},
    "negativeBalance": {"amount": 3, "period": "YEAR", "shouldReset": True},
    "automaticTimeEntryCreation": {"enabled": True, "defaultEntities": {"projectId": "p1", "taskId": "t1"}},
    "userIds": ["u1"],
    "userGroupIds": ["g1"],
}


def test_build_policy_update_carries_over_everything_not_changed() -> None:
    # Arrange
    current = TimeOffPolicy.model_validate(STORED)
    # Act
    payload = build_policy_update(current, PolicyChanges())
    # Assert
    assert payload.model_dump(mode="json", by_alias=True, exclude_none=True) == {
        "name": "Vacation",
        "approve": {"requiresApproval": True, "specificMembers": True, "teamManagers": True, "userIds": ["u1"]},
        "allowHalfDay": False,
        "allowNegativeBalance": False,
        "archived": True,
        "everyoneIncludingNew": False,
        "hasExpiration": True,
        "color": "#fff",
        "users": {"ids": ["u1"], "contains": "CONTAINS"},
        "userGroups": {"ids": ["g1"], "contains": "CONTAINS"},
        "negativeBalance": {"amount": 3.0, "period": "YEAR", "shouldReset": True},
        "automaticTimeEntryCreation": {"defaultEntities": {"projectId": "p1", "taskId": "t1"}, "enabled": True},
    }


def test_build_policy_update_applies_the_requested_changes() -> None:
    # Arrange
    current = TimeOffPolicy.model_validate(STORED)
    changes = PolicyChanges(
        name="Leave",
        icon=TimeOffPolicyIcon.PLANE,
        requires_approval=False,
        allow_half_day=True,
        users=["u2"],
        groups=["g2"],
    )
    # Act
    payload = build_policy_update(current, changes)
    # Assert
    assert payload.model_dump(mode="json", by_alias=True, exclude_none=True) == {
        "name": "Leave",
        "approve": {"requiresApproval": False, "specificMembers": True, "teamManagers": True, "userIds": ["u1"]},
        "allowHalfDay": True,
        "allowNegativeBalance": False,
        "archived": True,
        "everyoneIncludingNew": False,
        "hasExpiration": True,
        "color": "#fff",
        "icon": "PLANE",
        "users": {"ids": ["u2"], "contains": "CONTAINS"},
        "userGroups": {"ids": ["g2"], "contains": "CONTAINS"},
        "negativeBalance": {"amount": 3.0, "period": "YEAR", "shouldReset": True},
        "automaticTimeEntryCreation": {"defaultEntities": {"projectId": "p1", "taskId": "t1"}, "enabled": True},
    }


def test_member_filter_is_empty_without_ids() -> None:
    # Arrange
    ids: list[str] = []
    # Act
    result = member_filter(ids)
    # Assert
    assert result is None


def test_approval_marks_specific_members_when_approvers_are_given() -> None:
    # Arrange
    approvers = ["u1"]
    # Act
    result = approval(requires_approval=True, approvers=approvers, team_managers=False)
    # Assert
    assert result.model_dump(mode="json", by_alias=True) == {
        "requiresApproval": True,
        "specificMembers": True,
        "teamManagers": False,
        "userIds": ["u1"],
    }
