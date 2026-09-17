import sys
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from clockify import Region

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.config.settings import Profile
from clockify_unofficial_cli.output.columns import AUTH_STATUS
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from clockify import User

    from clockify_unofficial_cli.auth.credentials import WritableCredentialStore
    from clockify_unofficial_cli.auth.resolver import CredentialStores
    from clockify_unofficial_cli.runtime.context import AppContext

APP: Final = typer.Typer(help="Log in, inspect, and remove Clockify credentials.", no_args_is_help=True)


def _read_api_key(*, with_token: bool) -> str:
    # No --api-key flag on purpose: a key passed as an argument ends up in shell history.
    raw = sys.stdin.read() if with_token else typer.prompt("Clockify API key", hide_input=True, err=True)
    api_key = str(raw).strip()
    if not api_key:
        message = "The API key is empty."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return api_key


def _select_store(stores: CredentialStores, *, insecure_storage: bool) -> WritableCredentialStore:
    if insecure_storage:
        return stores.file
    if stores.keyring.available():
        return stores.keyring
    message = "No system keyring backend is available."
    raise CliError(
        message,
        exit_code=ExitCode.CONFIGURATION,
        hint="Retry with --insecure-storage, or set CLOCKIFY_API_KEY in the environment.",
    )


def _save_profile(app_context: AppContext, user: User, region: Region) -> Profile:
    options = app_context.options
    store = app_context.services.settings
    workspace_id = options.workspace_id or user.active_workspace or user.default_workspace
    profile = Profile(region=region, workspace_id=workspace_id, user_id=user.id, email=user.email)
    settings = store.load()
    if not settings.profiles:
        settings = settings.model_copy(update={"default_profile": options.profile_name})
    store.save(settings.with_profile(options.profile_name, profile))
    return profile


@APP.command(help="Validate an API key and store it for the selected profile.")
@handle_errors
def login(
    ctx: typer.Context,
    *,
    region: Annotated[
        Region | None,
        typer.Option("--region", help="Clockify data region; defaults to the profile's, else GLOBAL."),
    ] = None,
    with_token: Annotated[bool, typer.Option("--with-token", help="Read the API key from standard input.")] = False,
    insecure_storage: Annotated[
        bool,
        typer.Option("--insecure-storage", help="Store the key in a 0600 plaintext file instead of the keyring."),
    ] = False,
) -> None:
    app_context = get_app_context(ctx)
    stores = app_context.services.credentials
    profile_name = app_context.options.profile_name
    credential = ApiKeyCredential(api_key=_read_api_key(with_token=with_token))
    resolved_region = region or app_context.options.profile.region

    with app_context.services.clients(credential, resolved_region) as client:
        user = client.user.me()

    store = _select_store(stores, insecure_storage=insecure_storage)
    store.set(profile_name, credential)
    for other in stores.writable():
        if other is not store:
            other.delete(profile_name)
    profile = _save_profile(app_context, user, resolved_region)

    app_context.notify(f"Logged in to profile '{profile_name}' as {user.email} ({store.source}).")
    record = {
        "profile": profile_name,
        "name": user.name,
        "email": user.email,
        "workspaceId": profile.workspace_id,
        "region": profile.region,
        "source": store.source,
        "apiKey": credential.masked(),
    }
    app_context.render(single(record, AUTH_STATUS))


@APP.command(help="Show the active credential and the user it belongs to.")
@handle_errors
def status(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    resolved = app_context.credential()
    user = app_context.client().user.me()
    record = {
        "profile": app_context.options.profile_name,
        "name": user.name,
        "email": user.email,
        "workspaceId": app_context.options.workspace_id or user.active_workspace,
        "region": app_context.options.profile.region,
        "source": resolved.source,
        "apiKey": resolved.credential.masked(),
    }
    app_context.render(single(record, AUTH_STATUS))


@APP.command(help="Remove the stored credential and profile.")
@handle_errors
def logout(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    services = app_context.services
    profile_name = app_context.options.profile_name

    removed = [store.source for store in services.credentials.writable() if store.delete(profile_name)]
    settings = services.settings.load()
    had_profile = profile_name in settings.profiles
    if had_profile:
        services.settings.save(settings.without_profile(profile_name))
    if not removed and not had_profile:
        message = f"No stored credentials for profile '{profile_name}'."
        raise CliError(message, exit_code=ExitCode.CONFIGURATION)

    app_context.notify(f"Logged out of profile '{profile_name}'.")
    if services.credentials.environment.get(profile_name) is not None:
        app_context.notify("CLOCKIFY_API_KEY is still set in the environment and will keep being used.")


@APP.command(help="Print the raw API key of the active credential.")
@handle_errors
def token(ctx: typer.Context) -> None:
    resolved = get_app_context(ctx).credential()
    typer.echo(resolved.credential.api_key)
