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
REPORTS_URL: Final = f"https://reports.api.clockify.me/v1/workspaces/{WORKSPACE}/reports"
RANGE: Final = ["--from", "2026-09-01", "--to", "2026-09-30"]
PROJECT: Final = {"id": "777777777777777777777777", "name": "Website", "workspaceId": WORKSPACE, "archived": False}
TOTALS: Final = [{"totalTime": 5400, "totalBillableTime": 3600, "entriesCount": 3}]


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))


@respx.mock
def test_report_summary_flattens_groups_and_sends_the_request(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{BASE_URL}/workspaces/{WORKSPACE}/projects").mock(return_value=Response(200, json=[PROJECT]))
    group = {"_id": PROJECT["id"], "name": "Website", "duration": 5400, "children": []}
    route = respx.post(f"{REPORTS_URL}/summary").mock(
        return_value=Response(200, json={"totals": TOTALS, "groupOne": [group]})
    )
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "report", "summary", *RANGE, "-P", "Website", "--billable", "--group-by", "PROJECT"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "dateRangeStart": "2026-09-01T00:00:00Z",
        "dateRangeEnd": "2026-09-30T00:00:00Z",
        "billable": True,
        "projects": {"ids": [PROJECT["id"]], "contains": "CONTAINS"},
        "summaryFilter": {"groups": ["PROJECT"]},
        "exportType": "JSON",
    }
    assert json.loads(result.stdout) == [{"level": 1, "id": PROJECT["id"], "name": "Website", "duration": 5400}]
    assert "Total: 5400s (3600s billable) in 3 entries." in result.stderr


@respx.mock
def test_report_detailed_pages_through_entries(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    entry = {"_id": "e1", "description": "focus", "timeInterval": {"start": "2026-09-01T09:00:00Z", "duration": 1800}}
    route = respx.post(f"{REPORTS_URL}/detailed").mock(
        return_value=Response(200, json={"totals": TOTALS, "timeentries": [entry]})
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "report", "detailed", *RANGE, "--page", "2", "--page-size", "10"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content)["detailedFilter"] == {"page": 2, "pageSize": 10}
    assert json.loads(result.stdout) == [entry]


@respx.mock
def test_report_weekly_sends_group_and_subgroup(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{REPORTS_URL}/weekly").mock(return_value=Response(200, json={"totals": [], "groupOne": []}))
    # Act
    result = runner.invoke(
        cli,
        ["-o", "json", "report", "weekly", "--period", "last-week", "--group", "PROJECT", "--subgroup", "EARNINGS"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content)["weeklyFilter"] == {"group": "PROJECT", "subgroup": "EARNINGS"}
    assert json.loads(result.stdout) == []


@respx.mock
def test_report_rejects_a_period_combined_with_a_range(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["report", "summary", "--period", "today", "--from", "2026-09-01"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_report_unknown_project_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{BASE_URL}/workspaces/{WORKSPACE}/projects").mock(return_value=Response(200, json=[PROJECT]))
    # Act
    result = runner.invoke(cli, ["report", "summary", *RANGE, "-P", "Missing"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_shared_report_generate_renders_the_payload_keys(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    payload = {"totals": TOTALS, "groupOne": []}
    route = respx.get("https://reports.api.clockify.me/v1/shared-reports/abc123").mock(
        return_value=Response(200, json=payload)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "shared-report", "generate", "abc123", "--page", "2"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.calls.last.request.url.params["page"] == "2"
    assert json.loads(result.stdout) == payload
