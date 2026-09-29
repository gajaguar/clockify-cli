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

PROJECT_PAYLOAD: Final = {
    "id": "111111111111111111111111",
    "name": "Internal",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
    "clientId": None,
    "archived": False,
    "public": True,
    "billable": True,
    "color": "#0f62fe",
    "note": "first project",
    "estimate": None,
    "estimateType": None,
    "hourlyRate": None,
    "costRate": None,
    "memberships": None,
}


def _project_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/projects"


@respx.mock
def test_project_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_project_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[PROJECT_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "project", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [PROJECT_PAYLOAD]


@respx.mock
def test_project_create_maps_public_to_is_public(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(_project_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(201, json=PROJECT_PAYLOAD)
    )
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "project",
            "create",
            "--name",
            "Internal",
            "--public",
            "--color",
            "#0f62fe",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Internal", "isPublic": True, "color": "#0f62fe"}


@respx.mock
def test_project_update_omits_unchanged_fields(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_project_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[PROJECT_PAYLOAD]))
    route = respx.put(f"{_project_path(USER_PAYLOAD['activeWorkspace'])}/{PROJECT_PAYLOAD['id']}").mock(
        return_value=Response(200, json=PROJECT_PAYLOAD)
    )
    # Act
    result = runner.invoke(
        cli,
        ["-o", "json", "project", "update", PROJECT_PAYLOAD["id"], "--no-billable"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"billable": False}


@respx.mock
def test_project_get_unknown_name_exits_not_found(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_project_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[PROJECT_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["project", "get", "Ghost"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_project_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_project_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[PROJECT_PAYLOAD]))
    route = respx.delete(f"{_project_path(USER_PAYLOAD['activeWorkspace'])}/{PROJECT_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["project", "delete", PROJECT_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
