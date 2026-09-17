from typing import Annotated
from typing import Final

import typer

from clockify_unofficial_cli.output.columns import PROFILES
from clockify_unofficial_cli.output.renderer import Dataset
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

APP: Final = typer.Typer(help="Inspect and edit local CLI configuration.", no_args_is_help=True)


@APP.command(help="Print the settings file location.")
@handle_errors
def path(ctx: typer.Context) -> None:
    typer.echo(str(get_app_context(ctx).services.settings.path))


@APP.command(name="list", help="List configured profiles.")
@handle_errors
def list_profiles(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    settings = app_context.services.settings.load()
    records = [
        {
            "name": name,
            "default": name == settings.default_profile,
            "region": profile.region,
            "workspaceId": profile.workspace_id,
            "email": profile.email,
        }
        for name, profile in sorted(settings.profiles.items())
    ]
    app_context.render(Dataset(records=records, columns=PROFILES))


@APP.command(help="Set the default profile.")
@handle_errors
def use(ctx: typer.Context, name: Annotated[str, typer.Argument(help="Name of an existing profile.")]) -> None:
    app_context = get_app_context(ctx)
    store = app_context.services.settings
    settings = store.load()
    if name not in settings.profiles:
        message = f"Unknown profile '{name}'."
        raise CliError(message, exit_code=ExitCode.CONFIGURATION, hint="Run `clockify config list`.")
    store.save(settings.model_copy(update={"default_profile": name}))
    app_context.notify(f"Default profile set to '{name}'.")
