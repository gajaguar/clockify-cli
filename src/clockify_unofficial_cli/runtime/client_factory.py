from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from clockify import ClientOptions
from clockify import ClockifyClient
from clockify import Region

if TYPE_CHECKING:
    from clockify_unofficial_cli.auth.credentials import Credential

type ClientFactory = Callable[[Credential, Region], ClockifyClient]  # pylint: disable=app-module-const-naming


def create_sdk_client(credential: Credential, region: Region) -> ClockifyClient:
    return ClockifyClient(api_key=credential.api_key, options=ClientOptions(region=region))
