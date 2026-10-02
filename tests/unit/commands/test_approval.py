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
APPROVALS: Final = f"{BASE_URL}/workspaces/{WORKSPACE}/approval-requests"
REQUEST_ID: Final = "121212121212121212121212"
REQUEST: Final = {
    "id": REQUEST_ID,
    "workspaceId": WORKSPACE,
    "type": "TIMESHEET",
    "status": {"state": "PENDING"},
    "owner": {"userId": USER_PAYLOAD["id"], "userName": "Some One"},
    "dateRange": {"start": "2026-09-14T00:00:00Z", "end": "2026-09-20T23:59:59Z"},
}


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{BASE_URL}/workspaces/{WORKSPACE}/users").mock(return_value=Response(200, json=[USER_PAYLOAD]))


@respx.mock
def test_approval_list_sends_the_filters(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.get(APPROVALS).mock(return_value=Response(200, json=[{"approvalRequest": REQUEST}]))
    # Act
    result = runner.invoke(
        cli,
        ["-o", "json", "approval", "list", "--status", "PENDING", "--type", "TIMESHEET", "--sort-order", "ASCENDING"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert dict(route.calls.last.request.url.params) == {
        "status": "PENDING",
        "types": "TIMESHEET",
        "sort-order": "ASCENDING",
        "page": "1",
        "page-size": "200",
    }
    assert [row["approvalRequest"]["id"] for row in json.loads(result.stdout)] == [REQUEST_ID]


@respx.mock
def test_approval_submit_posts_the_period(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{APPROVALS}/TIMESHEET").mock(return_value=Response(201, json=REQUEST))
    # Act
    result = runner.invoke(cli, ["-o", "json", "approval", "submit", "--start", "2026-09-14", "--period", "WEEKLY"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {"periodStart": "2026-09-14T00:00:00Z", "period": "WEEKLY"}


@respx.mock
def test_approval_submit_for_another_user(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{APPROVALS}/users/{USER_PAYLOAD['id']}/EXPENSE").mock(
        return_value=Response(201, json=REQUEST)
    )
    # Act
    result = runner.invoke(
        cli,
        ["approval", "submit", "--start", "2026-09-14", "--type", "EXPENSE", "--user", USER_PAYLOAD["id"]],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_approval_resubmit_posts_the_entries(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{APPROVALS}/resubmit-entries-for-approval").mock(return_value=Response(200, json=REQUEST))
    # Act
    result = runner.invoke(
        cli, ["approval", "resubmit", "--start", "2026-09-14", "--type", "TIMESHEET", "--period", "WEEKLY"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "periodStart": "2026-09-14T00:00:00Z",
        "period": "WEEKLY",
        "type": "TIMESHEET",
    }


@respx.mock
def test_approval_decisions_change_the_state(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.patch(f"{APPROVALS}/{REQUEST_ID}").mock(return_value=Response(200, json=REQUEST))
    # Act
    approved = runner.invoke(cli, ["approval", "approve", REQUEST_ID, "--note", "ok"])
    rejected = runner.invoke(cli, ["approval", "reject", REQUEST_ID])
    withdrawn = runner.invoke(cli, ["approval", "withdraw", REQUEST_ID])
    unapproved = runner.invoke(cli, ["approval", "withdraw", REQUEST_ID, "--approval"])
    # Assert
    exit_codes = [result.exit_code for result in (approved, rejected, withdrawn, unapproved)]
    assert exit_codes == [ExitCode.OK] * 4
    assert [json.loads(call.request.content) for call in route.calls] == [
        {"state": "APPROVED", "note": "ok"},
        {"state": "REJECTED"},
        {"state": "WITHDRAWN_SUBMISSION"},
        {"state": "WITHDRAWN_APPROVAL"},
    ]


@respx.mock
def test_approval_forbidden_maps_to_its_exit_code(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.patch(f"{APPROVALS}/{REQUEST_ID}").mock(return_value=Response(403, json={"message": "no", "code": 403}))
    # Act
    result = runner.invoke(cli, ["approval", "approve", REQUEST_ID])
    # Assert
    assert result.exit_code == ExitCode.FORBIDDEN
