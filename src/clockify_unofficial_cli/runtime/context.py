from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from clockify import UserId
from rich.console import Console

from clockify_unofficial_cli.runtime.client_factory import ClientRequest
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    import typer
    from clockify import ClockifyClient
    from clockify import WorkspaceClient

    from clockify_unofficial_cli.auth.credentials import ResolvedCredential
    from clockify_unofficial_cli.auth.resolver import CredentialStores
    from clockify_unofficial_cli.config.settings import ResolvedOptions
    from clockify_unofficial_cli.config.store import SettingsStore
    from clockify_unofficial_cli.output.renderer import Dataset
    from clockify_unofficial_cli.output.renderer import Renderer
    from clockify_unofficial_cli.runtime.client_factory import ClientFactory


@dataclass(frozen=True, slots=True)
class Services:
    settings: SettingsStore
    credentials: CredentialStores
    clients: ClientFactory


# Built once per invocation by the root callback and shared with every command through
# typer.Context.obj; the SDK client is created lazily so offline commands never need a key.
@dataclass(slots=True)
class AppContext:
    options: ResolvedOptions
    services: Services
    console: Console
    renderer: Renderer
    _client: ClockifyClient | None = field(default=None, init=False, repr=False)
    _user_id: UserId | None = field(default=None, init=False, repr=False)

    def credential(self) -> ResolvedCredential:
        resolved = self.services.credentials.resolve(self.options.profile_name)
        if resolved is None:
            message = f"Not logged in (profile '{self.options.profile_name}')."
            hint = "Run `clockify auth login` or set CLOCKIFY_API_KEY."
            raise CliError(message, exit_code=ExitCode.CONFIGURATION, hint=hint)
        return resolved

    def client(self) -> ClockifyClient:
        if self._client is None:
            credential = self.credential().credential
            request = ClientRequest(
                credential=credential,
                region=self.options.profile.region,
                verbose=self.options.verbose,
            )
            self._client = self.services.clients(request)
        return self._client

    def user_id(self) -> UserId:
        if self._user_id is None:
            cached = self.options.profile.user_id
            if cached is not None:
                self._user_id = UserId(cached)
            else:
                self._user_id = self.client().user.me().id
        return self._user_id

    def workspace(self) -> WorkspaceClient:
        if self.options.workspace_id:
            return self.client().workspace(self.options.workspace_id)
        return self.client().default_workspace()

    # Status messages go to stderr so stdout stays clean for piping rendered data.
    @staticmethod
    def notify(message: str) -> None:
        Console(stderr=True, highlight=False).print(message, markup=False)

    def render(self, dataset: Dataset) -> None:
        self.renderer.render(dataset)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        self._user_id = None


def get_app_context(ctx: typer.Context) -> AppContext:
    obj: object = ctx.find_root().obj
    if not isinstance(obj, AppContext):
        message = "CLI context is not initialized."
        raise CliError(message)
    return obj
