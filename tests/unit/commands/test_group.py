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

GROUP_PAYLOAD: Final = {
    "id": "555555555555555555555555",
    "name": "Engineering",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
    "userIds": None,
    "teamManagers": None,
}


def _group_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/user-groups"


@respx.mock
def test_group_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_group_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[GROUP_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "group", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [GROUP_PAYLOAD]


@respx.mock
def test_group_create_posts_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(_group_path(USER_PAYLOAD["activeWorkspace"])).mock(
        return_value=Response(201, json=GROUP_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "group", "create", "--name", "Engineering"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Engineering"}


@respx.mock
def test_group_update_requires_name(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_group_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[GROUP_PAYLOAD]))
    route = respx.put(f"{_group_path(USER_PAYLOAD['activeWorkspace'])}/{GROUP_PAYLOAD['id']}").mock(
        return_value=Response(200, json=GROUP_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "group", "update", "Engineering", "--name", "Platform"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Platform"}


@respx.mock
def test_group_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_group_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[GROUP_PAYLOAD]))
    route = respx.delete(f"{_group_path(USER_PAYLOAD['activeWorkspace'])}/{GROUP_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["group", "delete", GROUP_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
