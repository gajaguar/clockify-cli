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

TAG_PAYLOAD: Final = {
    "id": "222222222222222222222222",
    "name": "billing",
    "workspaceId": USER_PAYLOAD["activeWorkspace"],
    "archived": False,
}


def _tag_path(workspace_id: str) -> str:
    return f"{BASE_URL}/workspaces/{workspace_id}/tags"


@respx.mock
def test_tag_list_renders_rows(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_tag_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TAG_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "tag", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == [TAG_PAYLOAD]


@respx.mock
def test_tag_create_posts_payload(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    route = respx.post(_tag_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(201, json=TAG_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "tag", "create", "--name", "billing"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "billing"}


@respx.mock
def test_tag_update_omits_unchanged_fields(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_tag_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TAG_PAYLOAD]))
    route = respx.put(f"{_tag_path(USER_PAYLOAD['activeWorkspace'])}/{TAG_PAYLOAD['id']}").mock(
        return_value=Response(200, json=TAG_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "tag", "update", TAG_PAYLOAD["id"], "--archived"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"archived": True}


@respx.mock
def test_tag_get_unknown_name_exits_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_tag_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TAG_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["tag", "get", "Zzz"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_tag_delete_sends_yes_skip(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(_tag_path(USER_PAYLOAD["activeWorkspace"])).mock(return_value=Response(200, json=[TAG_PAYLOAD]))
    route = respx.delete(f"{_tag_path(USER_PAYLOAD['activeWorkspace'])}/{TAG_PAYLOAD['id']}").mock(
        return_value=Response(204)
    )
    # Act
    result = runner.invoke(cli, ["tag", "delete", TAG_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
