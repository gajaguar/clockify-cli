from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    import typer
    from typer.testing import CliRunner

WORKSPACE: Final = USER_PAYLOAD["activeWorkspace"]
OFF: Final = f"{BASE_URL}/workspaces/{WORKSPACE}/time-off"
POLICY_ID: Final = "888888888888888888888888"
REQUEST_ID: Final = "999999999999999999999999"
POLICY: Final = {
    "id": POLICY_ID,
    "workspaceId": WORKSPACE,
    "name": "Vacation",
    "archived": False,
    "timeUnit": "DAYS",
    "allowHalfDay": True,
    "allowNegativeBalance": False,
    "everyoneIncludingNew": False,
    "approve": {"requiresApproval": True, "specificMembers": False, "teamManagers": False, "userIds": []},
    "automaticAccrual": {"amount": 1.5, "period": "MONTH", "timeUnit": "DAYS"},
    "userIds": [USER_PAYLOAD["id"]],
    "userGroupIds": [],
}
REQUEST: Final = {
    "id": REQUEST_ID,
    "workspaceId": WORKSPACE,
    "policyId": POLICY_ID,
    "policyName": "Vacation",
    "userId": USER_PAYLOAD["id"],
    "userName": "Some One",
    "balanceDiff": -2.0,
    "status": {"statusType": "PENDING"},
    "timeOffPeriod": {"period": {"start": "2026-09-14T00:00:00Z", "end": "2026-09-15T00:00:00Z"}},
}
BALANCE: Final = {"userId": USER_PAYLOAD["id"], "userName": "Some One", "policyName": "Vacation", "balance": 8.0}


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{OFF}/policies").mock(return_value=Response(200, json=[POLICY]))
    respx.get(f"{BASE_URL}/workspaces/{WORKSPACE}/users").mock(return_value=Response(200, json=[USER_PAYLOAD]))


@respx.mock
def test_policy_list_sends_the_filter(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["-o", "json", "time-off", "policy", "list", "--status", "ACTIVE", "--name", "Vac"])
    # Assert
    assert result.exit_code == ExitCode.OK
    params = respx.calls.last.request.url.params
    assert dict(params) == {"name": "Vac", "status": "ACTIVE", "page": "1", "page-size": "200"}
    assert [row["id"] for row in json.loads(result.stdout)] == [POLICY_ID]


@respx.mock
def test_policy_get_resolves_the_name(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.get(f"{OFF}/policies/{POLICY_ID}").mock(return_value=Response(200, json=POLICY))
    # Act
    result = runner.invoke(cli, ["-o", "json", "time-off", "policy", "get", "Vacation"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_policy_create_posts_approval_and_membership(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{OFF}/policies").mock(return_value=Response(201, json=POLICY))
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "time-off", "policy", "create", "--name", "Vacation", "--unit", "DAYS"),
            *("--requires-approval", "--approver", USER_PAYLOAD["id"], "--allow-half-day"),
            *("--user", USER_PAYLOAD["id"], "--accrual-amount", "1.5", "--accrual-period", "MONTH"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "name": "Vacation",
        "approve": {
            "requiresApproval": True,
            "specificMembers": True,
            "teamManagers": False,
            "userIds": [USER_PAYLOAD["id"]],
        },
        "allowHalfDay": True,
        "allowNegativeBalance": False,
        "everyoneIncludingNew": False,
        "timeUnit": "DAYS",
        "users": {"ids": [USER_PAYLOAD["id"]], "contains": "CONTAINS"},
        "automaticAccrual": {"amount": 1.5, "period": "MONTH"},
    }


@respx.mock
def test_policy_update_keeps_what_the_options_leave_out(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    item = f"{OFF}/policies/{POLICY_ID}"
    respx.get(item).mock(return_value=Response(200, json=POLICY))
    route = respx.put(item).mock(return_value=Response(200, json=POLICY))
    # Act
    result = runner.invoke(cli, ["-o", "json", "time-off", "policy", "update", "Vacation", "--no-half-day"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "name": "Vacation",
        "approve": {
            "requiresApproval": True,
            "specificMembers": False,
            "teamManagers": False,
            "userIds": [],
        },
        "allowHalfDay": False,
        "allowNegativeBalance": False,
        "archived": False,
        "everyoneIncludingNew": False,
        "hasExpiration": False,
        "users": {"ids": [USER_PAYLOAD["id"]], "contains": "CONTAINS"},
        "automaticAccrual": {"amount": 1.5, "period": "MONTH"},
    }


@respx.mock
def test_policy_archive_and_restore_change_the_status(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.patch(f"{OFF}/policies/{POLICY_ID}").mock(return_value=Response(200, json=POLICY))
    # Act
    archived = runner.invoke(cli, ["-o", "json", "time-off", "policy", "archive", "Vacation"])
    restored = runner.invoke(cli, ["-o", "json", "time-off", "policy", "restore", "Vacation"])
    # Assert
    assert (archived.exit_code, restored.exit_code) == (ExitCode.OK, ExitCode.OK)
    assert [json.loads(call.request.content) for call in route.calls] == [{"status": "ARCHIVED"}, {"status": "ACTIVE"}]


@respx.mock
def test_policy_delete_with_yes(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.delete(f"{OFF}/policies/{POLICY_ID}").mock(return_value=Response(204))
    # Act
    result = runner.invoke(cli, ["time-off", "policy", "delete", "Vacation", "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_policy_unknown_name_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["time-off", "policy", "get", "Sabbatical"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_request_list_posts_the_filter_in_the_body(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{OFF}/requests").mock(return_value=Response(200, json={"requests": [REQUEST], "count": 1}))
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "time-off", "request", "list", "--status", "PENDING", "--user", USER_PAYLOAD["id"]]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "statuses": ["PENDING"],
        "users": [USER_PAYLOAD["id"]],
        "page": 1,
        "pageSize": 200,
    }
    assert [row["id"] for row in json.loads(result.stdout)] == [REQUEST_ID]


@respx.mock
def test_request_create_sends_the_period(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{OFF}/policies/{POLICY_ID}/requests").mock(return_value=Response(201, json=REQUEST))
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "time-off",
            "request",
            "create",
            "-P",
            "Vacation",
            "--from",
            "2026-09-14",
            "--to",
            "2026-09-15",
            "--note",
            "trip",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "timeOffPeriod": {"period": {"start": "2026-09-14", "end": "2026-09-15"}},
        "note": "trip",
    }


@respx.mock
def test_request_create_half_day_for_another_user(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{OFF}/policies/{POLICY_ID}/users/{USER_PAYLOAD['id']}/requests").mock(
        return_value=Response(201, json=REQUEST)
    )
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "time-off",
            "request",
            "create",
            "-P",
            "Vacation",
            "--from",
            "2026-09-14",
            "--half-day",
            "FIRST_HALF",
            "--user",
            USER_PAYLOAD["id"],
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "timeOffPeriod": {
            "period": {"start": "2026-09-14", "end": "2026-09-14"},
            "isHalfDay": True,
            "halfDayPeriod": "FIRST_HALF",
        }
    }


@respx.mock
def test_request_approve_finds_the_policy_from_the_listing(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.post(f"{OFF}/requests").mock(return_value=Response(200, json={"requests": [REQUEST], "count": 1}))
    route = respx.patch(f"{OFF}/policies/{POLICY_ID}/requests/{REQUEST_ID}").mock(
        return_value=Response(200, json={"id": REQUEST_ID, "policyId": POLICY_ID})
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "time-off", "request", "approve", REQUEST_ID, "--note", "enjoy"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {"status": "APPROVED", "note": "enjoy"}


@respx.mock
def test_request_reject_with_an_explicit_policy(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.patch(f"{OFF}/policies/{POLICY_ID}/requests/{REQUEST_ID}").mock(
        return_value=Response(200, json={"id": REQUEST_ID})
    )
    # Act
    result = runner.invoke(cli, ["time-off", "request", "reject", REQUEST_ID, "--policy", "Vacation"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {"status": "REJECTED"}


@respx.mock
def test_request_decision_for_an_unknown_request_is_not_found(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.post(f"{OFF}/requests").mock(return_value=Response(200, json={"requests": [], "count": 0}))
    # Act
    result = runner.invoke(cli, ["time-off", "request", "approve", REQUEST_ID])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_request_delete_with_yes(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.delete(f"{OFF}/policies/{POLICY_ID}/requests/{REQUEST_ID}").mock(
        return_value=Response(200, json={"id": REQUEST_ID})
    )
    # Act
    result = runner.invoke(cli, ["time-off", "request", "delete", REQUEST_ID, "-P", POLICY_ID, "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_balance_list_by_policy_and_by_user(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    by_policy = respx.get(f"{OFF}/balance/policy/{POLICY_ID}").mock(
        return_value=Response(200, json={"balances": [BALANCE], "count": 1})
    )
    by_user = respx.get(f"{OFF}/balance/user/{USER_PAYLOAD['id']}").mock(
        return_value=Response(200, json={"balances": [BALANCE], "count": 1})
    )
    # Act
    first = runner.invoke(
        cli, ["-o", "json", "time-off", "balance", "list", "-P", "Vacation", "--sort-column", "USED"]
    )
    second = runner.invoke(cli, ["-o", "json", "time-off", "balance", "list", "--user", USER_PAYLOAD["id"]])
    # Assert
    assert (first.exit_code, second.exit_code) == (ExitCode.OK, ExitCode.OK)
    assert dict(by_policy.calls.last.request.url.params) == {"sort": "USED", "page": "1", "page-size": "200"}
    assert by_user.called


@respx.mock
def test_balance_list_needs_exactly_one_target(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    neither = runner.invoke(cli, ["time-off", "balance", "list"])
    both = runner.invoke(cli, ["time-off", "balance", "list", "-P", "Vacation", "--user", USER_PAYLOAD["id"]])
    # Assert
    assert (neither.exit_code, both.exit_code) == (ExitCode.USAGE, ExitCode.USAGE)


@respx.mock
def test_balance_update_sends_a_delta(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.patch(f"{OFF}/balance/policy/{POLICY_ID}").mock(return_value=Response(204))
    # Act
    result = runner.invoke(
        cli,
        [
            "time-off",
            "balance",
            "update",
            "-P",
            "Vacation",
            "--user",
            USER_PAYLOAD["id"],
            "--value",
            "2",
            "--from",
            "2026-01-01",
            "--note",
            "bonus",
            "--sync",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "userIds": [USER_PAYLOAD["id"]],
        "value": 2.0,
        "dateRange": {"start": "2026-01-01"},
        "note": "bonus",
        "sync": True,
    }


@respx.mock
def test_balance_assign_posts_the_assignment(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{OFF}/balance/assignment").mock(return_value=Response(204))
    # Act
    result = runner.invoke(
        cli,
        [
            *("time-off", "balance", "assign", "-P", "Vacation", "--user", USER_PAYLOAD["id"], "--balance", "10"),
            *("--from", "2026-01-01", "--to", "2026-12-31", "--note", "annual grant"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "policyId": POLICY_ID,
        "userIds": [USER_PAYLOAD["id"]],
        "balance": 10.0,
        "dateRange": {"start": "2026-01-01", "end": "2026-12-31"},
        "note": "annual grant",
    }


@respx.mock
def test_balance_assignments_update_and_delete(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    base = f"{OFF}/balance/assignment"
    listing = respx.get(f"{base}/user/{USER_PAYLOAD['id']}/policy/{POLICY_ID}").mock(
        return_value=Response(200, json=[{"id": "a1", "userId": USER_PAYLOAD["id"], "balance": 4.0}])
    )
    item = f"{base}/a1/user/{USER_PAYLOAD['id']}/policy/{POLICY_ID}"
    put = respx.put(item).mock(return_value=Response(204))
    delete = respx.delete(item).mock(return_value=Response(204))
    target = ["-P", "Vacation", "--user", USER_PAYLOAD["id"]]
    # Act
    listed = runner.invoke(cli, ["-o", "json", "time-off", "balance", "assignments", *target])
    updated = runner.invoke(
        cli,
        [
            "time-off",
            "balance",
            "update-assignment",
            "a1",
            *target,
            "--change",
            "-1",
            "--to",
            "2026-12-31",
            "--note",
            "fix",
        ],
    )
    deleted = runner.invoke(
        cli, ["time-off", "balance", "delete-assignment", "a1", *target, "--note", "mistake", "--yes"]
    )
    # Assert
    assert (listed.exit_code, updated.exit_code, deleted.exit_code) == (ExitCode.OK, ExitCode.OK, ExitCode.OK)
    assert listing.called
    assert json.loads(put.calls.last.request.content) == {
        "balanceChange": -1.0,
        "dateRange": {"end": "2026-12-31"},
        "note": "fix",
    }
    assert json.loads(delete.calls.last.request.content) == {"note": "mistake"}
