from __future__ import annotations

from typing import TYPE_CHECKING

from clockify.config import API_KEY_ENV_VAR

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.auth.credentials import CredentialSource

if TYPE_CHECKING:
    from collections.abc import Mapping


# The environment key is profile-agnostic: it overrides whatever profile is selected, for CI.
class EnvCredentialStore:
    def __init__(self, environ: Mapping[str, str]) -> None:
        self._environ = environ

    @property
    def source(self) -> CredentialSource:
        return CredentialSource.ENVIRONMENT

    def get(self, profile: str) -> ApiKeyCredential | None:
        del profile
        api_key = self._environ.get(API_KEY_ENV_VAR)
        return ApiKeyCredential(api_key=api_key) if api_key else None
