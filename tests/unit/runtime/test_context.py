from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest
import respx
from clockify import ClockifyClient
from clockify import Region
from httpx import Response
from rich.console import Console

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.config.settings import GlobalOptions
from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.config.settings import resolve_options
from clockify_unofficial_cli.output.formats import JsonRenderer
from clockify_unofficial_cli.output.renderer import RenderTarget
from clockify_unofficial_cli.runtime.client_factory import ClientRequest
from clockify_unofficial_cli.runtime.client_factory import create_sdk_client
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    from clockify_unofficial_cli.runtime.context import Services

CACHED_USER_ID: Final = USER_PAYLOAD["id"]


def _context(services: Services, workspace: str | None = None) -> AppContext:
    console = Console()
    options = resolve_options(GlobalOptions(workspace=workspace), Settings(), is_tty=False)
    renderer = JsonRenderer(RenderTarget(console=console, stream=console.file))
    return AppContext(options=options, services=services, console=console, renderer=renderer)


def test_explicit_workspace_binds_without_api_lookup(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    app_context = _context(services, workspace="ws-flag")
    # Act
    workspace = app_context.workspace()
    # Assert
    assert workspace.id == "ws-flag"
    app_context.close()


@respx.mock
def test_workspace_defaults_to_users_active_workspace(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    app_context = _context(services)
    # Act
    workspace = app_context.workspace()
    # Assert
    assert workspace.id == "64a1f0000000000000000001"
    app_context.close()


def test_client_is_created_once_per_invocation(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    app_context = _context(services)
    # Act
    first, second = app_context.client(), app_context.client()
    # Assert
    assert first is second
    app_context.close()


def test_get_app_context_requires_initialized_root() -> None:
    # Arrange
    ctx = type("Ctx", (), {"find_root": lambda self: self, "obj": None})()
    # Act
    with pytest.raises(CliError) as caught:
        get_app_context(ctx)
    # Assert
    assert caught.value.message == "CLI context is not initialized."


def test_sdk_client_factory_builds_client_for_region() -> None:
    # Arrange
    request = ClientRequest(credential=ApiKeyCredential(api_key="secret"), region=Region.EU_CENTRAL_1)
    # Act
    client = create_sdk_client(request)
    # Assert
    assert isinstance(client, ClockifyClient)
    client.close()


@respx.mock
def test_user_id_is_cached_from_profile(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    profile = Profile(user_id=CACHED_USER_ID)
    settings = Settings(profiles={"default": profile})
    options = resolve_options(GlobalOptions(), settings, is_tty=False)
    console = Console()
    context = AppContext(
        options=options,
        services=services,
        console=console,
        renderer=JsonRenderer(RenderTarget(console=console, stream=console.file)),
    )
    # Act
    resolved = context.user_id()
    # Assert
    assert resolved == CACHED_USER_ID
    assert context.options.profile == profile
    context.close()


@respx.mock
def test_user_id_falls_back_to_user_me(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    app_context = _context(services)
    # Act
    resolved = app_context.user_id()
    # Assert
    assert resolved == CACHED_USER_ID
    assert app_context.user_id() == resolved
    app_context.close()
