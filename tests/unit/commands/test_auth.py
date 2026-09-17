from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import keyring
import pytest
import respx
from clockify import Region
from httpx import Response
from keyring.backends.fail import Keyring as FailKeyring

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.auth.credentials import encode
from clockify_unofficial_cli.auth.keyring_store import SERVICE_NAME
from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.config.settings import Settings
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    from collections.abc import Iterator

    import typer
    from typer.testing import CliRunner

    from clockify_unofficial_cli.runtime.context import Services
    from tests.conftest import MemoryKeyring

API_KEY: Final = "test-api-key-1234"

LOGGED_IN_RECORD: Final = {
    "profile": "default",
    "name": "Some One",
    "email": "someone@example.com",
    "workspaceId": "64a1f0000000000000000001",
    "region": "GLOBAL",
    "source": "keyring",
    "apiKey": "********1234",
}


@pytest.fixture
def missing_keyring(memory_keyring: MemoryKeyring) -> Iterator[None]:
    keyring.set_keyring(FailKeyring())
    yield
    keyring.set_keyring(memory_keyring)


@respx.mock
def test_login_with_token_stores_key_in_keyring_and_saves_profile(
    runner: CliRunner, cli: typer.Typer, services: Services, memory_keyring: MemoryKeyring
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "auth", "login", "--with-token"], input=f"{API_KEY}\n")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == LOGGED_IN_RECORD
    assert memory_keyring.passwords == {(SERVICE_NAME, "default"): encode(ApiKeyCredential(api_key=API_KEY))}
    assert services.settings.load() == Settings(
        default_profile="default",
        profiles={
            "default": Profile(
                region=Region.GLOBAL,
                workspace_id="64a1f0000000000000000001",
                user_id="5b0f5b1f1f1f1f1f1f1f1f1f",
                email="someone@example.com",
            )
        },
    )


@respx.mock
def test_login_with_insecure_storage_writes_credentials_file(
    runner: CliRunner, cli: typer.Typer, services: Services, memory_keyring: MemoryKeyring
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(
        cli, ["-p", "work", "-o", "id", "auth", "login", "--with-token", "--insecure-storage"], input=API_KEY
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.credentials.file.get("work") == ApiKeyCredential(api_key=API_KEY)
    assert memory_keyring.passwords == {}
    assert services.settings.load().default_profile == "work"


@respx.mock
@pytest.mark.usefixtures("missing_keyring")
def test_login_without_keyring_backend_requires_explicit_insecure_storage(
    runner: CliRunner, cli: typer.Typer, services: Services
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["auth", "login", "--with-token"], input=API_KEY)
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "No system keyring backend is available." in result.stderr
    assert services.settings.load() == Settings()


def test_login_rejects_empty_key(runner: CliRunner, cli: typer.Typer) -> None:
    # Arrange
    empty_input = "   \n"
    # Act
    result = runner.invoke(cli, ["auth", "login", "--with-token"], input=empty_input)
    # Assert
    assert result.exit_code == ExitCode.USAGE
    assert "The API key is empty." in result.stderr


@respx.mock
def test_login_with_invalid_key_exits_with_authentication_code(
    runner: CliRunner, cli: typer.Typer, services: Services
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(401, json={"message": "Unauthorized", "code": 1000}))
    # Act
    result = runner.invoke(cli, ["auth", "login", "--with-token"], input=API_KEY)
    # Assert
    assert result.exit_code == ExitCode.AUTHENTICATION
    assert "Unauthorized (HTTP 401)" in result.stderr
    assert services.settings.load() == Settings()


@respx.mock
def test_status_reports_environment_credential(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = API_KEY
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "auth", "status"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == {**LOGGED_IN_RECORD, "source": "environment"}


def test_status_without_credentials_exits_with_configuration_code(runner: CliRunner, cli: typer.Typer) -> None:
    # Arrange
    args = ["auth", "status"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "Not logged in (profile 'default')." in result.stderr


def test_logout_removes_credential_and_profile(
    runner: CliRunner, cli: typer.Typer, services: Services, memory_keyring: MemoryKeyring
) -> None:
    # Arrange
    services.credentials.keyring.set("default", ApiKeyCredential(api_key=API_KEY))
    services.settings.save(Settings().with_profile("default", Profile()))
    # Act
    result = runner.invoke(cli, ["auth", "logout"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert memory_keyring.passwords == {}
    assert services.settings.load() == Settings()


def test_logout_warns_when_environment_key_remains(
    runner: CliRunner, cli: typer.Typer, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ["CLOCKIFY_API_KEY"] = API_KEY
    services.credentials.file.set("default", ApiKeyCredential(api_key=API_KEY))
    # Act
    result = runner.invoke(cli, ["auth", "logout"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "CLOCKIFY_API_KEY is still set" in result.stderr


def test_logout_without_stored_credentials_fails(runner: CliRunner, cli: typer.Typer) -> None:
    # Arrange
    args = ["auth", "logout"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "No stored credentials for profile 'default'." in result.stderr


def test_token_prints_raw_key(runner: CliRunner, cli: typer.Typer, services: Services) -> None:
    # Arrange
    services.credentials.keyring.set("default", ApiKeyCredential(api_key=API_KEY))
    # Act
    result = runner.invoke(cli, ["auth", "token"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert result.stdout == f"{API_KEY}\n"
