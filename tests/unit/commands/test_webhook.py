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
WEBHOOK_PAYLOAD: Final = {
    "id": "666666666666666666666666",
    "name": "Notify",
    "url": "https://example.test/hook",
    "workspaceId": WORKSPACE,
    "webhookEvent": "NEW_PROJECT",
    "triggerSource": [WORKSPACE],
    "triggerSourceType": "WORKSPACE_ID",
    "enabled": True,
    "authToken": "super-secret-token",
}


def _hooks() -> str:
    return f"{BASE_URL}/workspaces/{WORKSPACE}/webhooks"


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))


def _list_route() -> respx.Route:
    return respx.get(_hooks()).mock(
        return_value=Response(200, json={"webhooks": [WEBHOOK_PAYLOAD], "workspaceWebhookCount": 1})
    )


@respx.mock
def test_webhook_list_hides_the_signing_token(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = _list_route()
    # Act
    result = runner.invoke(cli, ["-o", "json", "webhook", "list", "--type", "USER_CREATED"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.calls.last.request.url.params["type"] == "USER_CREATED"
    assert "super-secret-token" not in result.stdout
    assert json.loads(result.stdout) == [
        {
            "id": WEBHOOK_PAYLOAD["id"],
            "name": "Notify",
            "url": "https://example.test/hook",
            "userId": None,
            "workspaceId": WORKSPACE,
            "webhookEvent": "NEW_PROJECT",
            "triggerSource": [WORKSPACE],
            "triggerSourceType": "WORKSPACE_ID",
            "enabled": True,
            "deliveryEnabled": None,
            "planEnabled": None,
        }
    ]


@respx.mock
def test_webhook_list_for_addon_uses_the_addon_route(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.get(f"{BASE_URL}/workspaces/{WORKSPACE}/addons/addon1/webhooks").mock(
        return_value=Response(200, json={"webhooks": [WEBHOOK_PAYLOAD]})
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "webhook", "list", "--addon", "addon1"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_webhook_get_resolves_name_and_hides_token(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _list_route()
    respx.get(f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}").mock(return_value=Response(200, json=WEBHOOK_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "webhook", "get", "Notify"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "authToken" not in result.stdout


@respx.mock
def test_webhook_create_defaults_the_source_to_the_workspace_and_shows_token(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(_hooks()).mock(return_value=Response(201, json=WEBHOOK_PAYLOAD))
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "webhook", "create", "--url", "https://example.test/hook", "--event", "NEW_PROJECT"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "url": "https://example.test/hook",
        "webhookEvent": "NEW_PROJECT",
        "triggerSource": [WORKSPACE],
        "triggerSourceType": "WORKSPACE_ID",
    }
    assert json.loads(result.stdout)["authToken"] == "super-secret-token"


@respx.mock
def test_webhook_update_keeps_unset_fields(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _list_route()
    item = f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}"
    respx.get(item).mock(return_value=Response(200, json=WEBHOOK_PAYLOAD))
    route = respx.put(item).mock(return_value=Response(200, json=WEBHOOK_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "webhook", "update", "Notify", "--url", "https://example.test/new"])
    # Assert
    assert result.exit_code == ExitCode.OK
    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "url": "https://example.test/new",
        "webhookEvent": "NEW_PROJECT",
        "triggerSource": [WORKSPACE],
        "triggerSourceType": "WORKSPACE_ID",
        "name": "Notify",
    }
    assert "super-secret-token" not in result.stdout


@respx.mock
def test_webhook_delete_with_yes(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _list_route()
    route = respx.delete(f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}").mock(return_value=Response(204))
    # Act
    result = runner.invoke(cli, ["webhook", "delete", WEBHOOK_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_webhook_rotate_token_prints_the_new_token(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _list_route()
    route = respx.patch(f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}/token").mock(
        return_value=Response(200, json=WEBHOOK_PAYLOAD)
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "webhook", "rotate-token", WEBHOOK_PAYLOAD["id"], "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
    assert json.loads(result.stdout)["authToken"] == "super-secret-token"


@respx.mock
def test_webhook_logs_posts_the_search_body(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _list_route()
    log = {"id": "l1", "webhookId": WEBHOOK_PAYLOAD["id"], "statusCode": 200}
    route = respx.post(f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}/logs").mock(return_value=Response(200, json=[log]))
    # Act
    result = runner.invoke(
        cli,
        [
            "-o",
            "json",
            "webhook",
            "logs",
            WEBHOOK_PAYLOAD["id"],
            "--status",
            "FAILED",
            "--newest-first",
            "--limit",
            "1",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {"status": "FAILED", "sortByNewest": True}
    assert json.loads(result.stdout)[0]["id"] == "l1"


@respx.mock
def test_webhook_statuses_filters_by_status(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _list_route()
    entry = {"id": "s1", "status": "FAILED", "statusCode": 500, "retryCount": 2}
    route = respx.get(f"{_hooks()}/{WEBHOOK_PAYLOAD['id']}/statuses").mock(return_value=Response(200, json=[entry]))
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "webhook", "statuses", WEBHOOK_PAYLOAD["id"], "--status", "FAILED", "--limit", "1"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.calls.last.request.url.params["statuses"] == "FAILED"


@respx.mock
def test_webhook_get_unknown_name_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _list_route()
    # Act
    result = runner.invoke(cli, ["webhook", "get", "Missing"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND
