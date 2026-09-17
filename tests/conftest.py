from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import keyring
import pytest
from clockify import NO_RETRY
from clockify import ClientOptions
from clockify import ClockifyClient
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from typer.testing import CliRunner

from clockify_unofficial_cli.auth.env_store import EnvCredentialStore
from clockify_unofficial_cli.auth.file_store import FileCredentialStore
from clockify_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from clockify_unofficial_cli.auth.resolver import CredentialStores
from clockify_unofficial_cli.config.store import SettingsStore
from clockify_unofficial_cli.main import create_app
from clockify_unofficial_cli.runtime.context import Services

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import typer
    from clockify import Region

    from clockify_unofficial_cli.auth.credentials import Credential

BASE_URL: Final = "https://fake.clockify.test/api/v1"

USER_PAYLOAD: Final = {
    "id": "5b0f5b1f1f1f1f1f1f1f1f1f",
    "email": "someone@example.com",
    "name": "Some One",
    "activeWorkspace": "64a1f0000000000000000001",
    "defaultWorkspace": "64a1f0000000000000000002",
    "status": "ACTIVE",
}


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.passwords[service, username] = password

    def delete_password(self, service: str, username: str) -> None:
        if (service, username) not in self.passwords:
            raise PasswordDeleteError(username)
        del self.passwords[service, username]


def fake_client(credential: Credential, region: Region) -> ClockifyClient:
    del region
    return ClockifyClient(api_key=credential.api_key, options=ClientOptions(base_url=BASE_URL, retry=NO_RETRY))


@pytest.fixture(name="memory_keyring")
def memory_keyring_fixture() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture(name="environ")
def environ_fixture() -> dict[str, str]:
    return {}


@pytest.fixture(name="services")
def services_fixture(tmp_path: Path, memory_keyring: MemoryKeyring, environ: dict[str, str]) -> Services:
    del memory_keyring
    return Services(
        settings=SettingsStore(tmp_path / "config.toml"),
        credentials=CredentialStores(
            environment=EnvCredentialStore(environ),
            keyring=KeyringCredentialStore(),
            file=FileCredentialStore(tmp_path / "credentials.toml"),
        ),
        clients=fake_client,
    )


@pytest.fixture
def cli(services: Services) -> typer.Typer:
    return create_app(lambda: services)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
