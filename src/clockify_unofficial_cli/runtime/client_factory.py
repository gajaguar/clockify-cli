from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from clockify import ClientOptions
from clockify import ClockifyClient
from clockify import Region

if TYPE_CHECKING:
    from clockify_unofficial_cli.auth.credentials import Credential


# Per-invocation bundle so the client factory can build a verbose request hook without
# growing a long positional argument list every time a new flag appears.
@dataclass(frozen=True, slots=True)
class ClientRequest:
    credential: Credential
    region: Region
    verbose: bool = False


type ClientFactory = Callable[[ClientRequest], ClockifyClient]  # pylint: disable=app-module-const-naming


def _log_response(response: object) -> None:
    raw_request = getattr(response, "request", None)
    method = getattr(raw_request, "method", "?")
    url = str(getattr(raw_request, "url", "?"))
    status = getattr(response, "status_code", "?")
    sys.stderr.write(f"-> {method} {url} {status}\n")
    sys.stderr.flush()


def create_sdk_client(request: ClientRequest) -> ClockifyClient:
    event_hooks: dict[str, list[Callable[..., object]]] | None = (
        {"response": [_log_response]} if request.verbose else None
    )
    options = ClientOptions(region=request.region, event_hooks=event_hooks)
    return ClockifyClient(api_key=request.credential.api_key, options=options)
