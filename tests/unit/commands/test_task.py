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

PROJECT_ID: Final = "111111111111111111111111"
PROJECT_FIXTURE: Final = {
    "id": PROJECT_ID,
    "name": "Internal",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
}
TASK_PAYLOAD: Final = {
    "id": "333333333333333333333333",
    "name": "Design",
    "projectId": PROJECT_ID,
    "assigneeIds": None,
    "estimate": "PT2H",
    "status": "ACTIVE",
    "duration": None,
    "hourlyRate": None,
    "costRate": None,
}


def _task_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/projects/{PROJECT_ID}/tasks"


def _projects_route(router: respx.MockRouter) -> None:
    router.get(f"{BASE_URL}/workspaces/{USER_PAYLOAD['activeWorkspace']}/projects").mock(
        return_value=Response(200, json=[PROJECT_FIXTURE])
    )


@respx.mock
def test_task_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    _projects_route(respx)
    respx.get(_task_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TASK_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "task", "list", "-P", "Internal"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [TASK_PAYLOAD]


@respx.mock
def test_task_create_posts_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    _projects_route(respx)
    route = respx.post(_task_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(201, json=TASK_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "task", "create", "-P", "Internal", "--name", "Design"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Design"}


@respx.mock
def test_task_update_omits_unchanged_fields(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    _projects_route(respx)
    respx.get(_task_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TASK_PAYLOAD]))
    route = respx.put(f"{_task_path(USER_PAYLOAD['activeWorkspace'])}/{TASK_PAYLOAD['id']}").mock(
        return_value=Response(200, json=TASK_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "task", "update", "Design", "-P", "Internal", "--status", "DONE"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"status": "DONE"}


@respx.mock
def test_task_get_unknown_name_exits_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    _projects_route(respx)
    respx.get(_task_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TASK_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["task", "get", "Zzz", "-P", "Internal"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_task_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    _projects_route(respx)
    respx.get(_task_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TASK_PAYLOAD]))
    route = respx.delete(f"{_task_path(USER_PAYLOAD['activeWorkspace'])}/{TASK_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["task", "delete", "Design", "-P", "Internal", "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
