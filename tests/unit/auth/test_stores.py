from __future__ import annotations

import stat
from typing import TYPE_CHECKING
from typing import Final

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.backends.fail import Keyring as FailKeyring
from keyring.errors import KeyringError

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.auth.credentials import CredentialSource
from clockify_unofficial_cli.auth.credentials import ResolvedCredential
from clockify_unofficial_cli.auth.env_store import EnvCredentialStore
from clockify_unofficial_cli.auth.file_store import FileCredentialStore
from clockify_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from clockify_unofficial_cli.runtime.errors import CliError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from clockify_unofficial_cli.runtime.context import Services
    from tests.conftest import MemoryKeyring

CREDENTIAL: Final = ApiKeyCredential(api_key="secret-key")


class RaisingKeyring(KeyringBackend):
    priority = 1

    def get_password(self, service: str, username: str) -> str | None:
        raise KeyringError(self.name)

    def set_password(self, service: str, username: str, password: str) -> None:
        raise KeyringError(self.name)

    def delete_password(self, service: str, username: str) -> None:
        raise KeyringError(self.name)


@pytest.fixture
def missing_keyring() -> Iterator[None]:
    previous = keyring.get_keyring()
    keyring.set_keyring(FailKeyring())
    yield
    keyring.set_keyring(previous)


@pytest.fixture
def raising_keyring() -> Iterator[None]:
    previous = keyring.get_keyring()
    keyring.set_keyring(RaisingKeyring())
    yield
    keyring.set_keyring(previous)


def test_environment_store_ignores_profile_name() -> None:
    # Arrange
    store = EnvCredentialStore({"CLOCKIFY_API_KEY": "secret-key"})
    # Act
    found = [store.get("default"), store.get("other")]
    # Assert
    assert found == [CREDENTIAL, CREDENTIAL]


def test_keyring_store_round_trips_and_deletes(memory_keyring: MemoryKeyring) -> None:
    # Arrange
    store = KeyringCredentialStore()
    store.set("work", CREDENTIAL)
    # Act
    stored = store.get("work")
    deleted = [store.delete("work"), store.delete("work")]
    # Assert
    assert stored == CREDENTIAL
    assert deleted == [True, False]
    assert memory_keyring.passwords == {}


@pytest.mark.usefixtures("missing_keyring")
def test_keyring_store_without_backend_is_unavailable() -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    state = (store.available(), store.get("work"), store.delete("work"))
    # Assert
    assert state == (False, None, False)


@pytest.mark.usefixtures("raising_keyring")
def test_keyring_store_read_failure_yields_nothing() -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    found = store.get("work")
    # Assert
    assert found is None


@pytest.mark.usefixtures("raising_keyring")
def test_keyring_store_write_failure_suggests_insecure_storage() -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    with pytest.raises(CliError) as caught:
        store.set("work", CREDENTIAL)
    # Assert
    assert caught.value.hint == "Retry with --insecure-storage to use a 0600 file instead."


def test_file_store_writes_owner_only_file_and_deletes_entries(tmp_path: Path) -> None:
    # Arrange
    store = FileCredentialStore(tmp_path / "nested" / "credentials.toml")
    store.set("work", CREDENTIAL)
    # Act
    stored = store.get("work")
    mode = stat.S_IMODE(store.path.stat().st_mode)
    deleted = [store.delete("work"), store.delete("work")]
    # Assert
    assert stored == CREDENTIAL
    assert mode == 0o600
    assert deleted == [True, False]
    assert store.get("work") is None


def test_resolve_prefers_environment_over_keyring_over_file(services: Services, environ: dict[str, str]) -> None:
    # Arrange
    stores = services.credentials
    stores.file.set("default", ApiKeyCredential(api_key="from-file"))
    stores.keyring.set("default", ApiKeyCredential(api_key="from-keyring"))
    before_env = stores.resolve("default")
    environ["CLOCKIFY_API_KEY"] = "from-env"
    # Act
    after_env = stores.resolve("default")
    # Assert
    assert before_env == ResolvedCredential(ApiKeyCredential(api_key="from-keyring"), CredentialSource.KEYRING)
    assert after_env == ResolvedCredential(ApiKeyCredential(api_key="from-env"), CredentialSource.ENVIRONMENT)
    assert stores.resolve("unknown") == ResolvedCredential(
        ApiKeyCredential(api_key="from-env"), CredentialSource.ENVIRONMENT
    )
