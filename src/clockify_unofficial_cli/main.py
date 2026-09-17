import os
import sys
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from rich.console import Console

from clockify_unofficial_cli._version import __version__
from clockify_unofficial_cli.auth.env_store import EnvCredentialStore
from clockify_unofficial_cli.auth.file_store import FileCredentialStore
from clockify_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from clockify_unofficial_cli.auth.resolver import CredentialStores
from clockify_unofficial_cli.commands import auth
from clockify_unofficial_cli.commands import client
from clockify_unofficial_cli.commands import config
from clockify_unofficial_cli.commands import custom_field
from clockify_unofficial_cli.commands import entry
from clockify_unofficial_cli.commands import group
from clockify_unofficial_cli.commands import project
from clockify_unofficial_cli.commands import tag
from clockify_unofficial_cli.commands import task
from clockify_unofficial_cli.commands import timer_shortcuts
from clockify_unofficial_cli.commands import user
from clockify_unofficial_cli.commands import workspace
from clockify_unofficial_cli.config.paths import credentials_file
from clockify_unofficial_cli.config.paths import settings_file
from clockify_unofficial_cli.config.settings import GlobalOptions
from clockify_unofficial_cli.config.settings import OutputFormat
from clockify_unofficial_cli.config.settings import resolve_options
from clockify_unofficial_cli.config.store import SettingsStore
from clockify_unofficial_cli.output.registry import create_renderer
from clockify_unofficial_cli.output.renderer import RenderTarget
from clockify_unofficial_cli.runtime.client_factory import create_sdk_client
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import Services
from clockify_unofficial_cli.runtime.errors import handle_errors

if TYPE_CHECKING:
    from collections.abc import Callable


def default_services() -> Services:
    return Services(
        settings=SettingsStore(settings_file()),
        credentials=CredentialStores(
            environment=EnvCredentialStore(os.environ),
            keyring=KeyringCredentialStore(),
            file=FileCredentialStore(credentials_file()),
        ),
        clients=create_sdk_client,
    )


def print_version(
    value: bool,  # ruff: ignore[boolean-type-hint-positional-argument]  Typer passes the flag value positionally
) -> None:
    if value:
        typer.echo(f"clockify {__version__}")
        raise typer.Exit


# Global options must precede the sub-command (`clockify -o json auth status`). Colors follow
# Rich's NO_COLOR handling, so there is no --no-color flag to keep the callback small.
def create_app(services_factory: Callable[[], Services] = default_services) -> typer.Typer:
    cli = typer.Typer(name="clockify", help="Unofficial command-line interface for Clockify.", no_args_is_help=True)

    @cli.callback()
    @handle_errors
    def root(  # ruff: ignore[PLR0913]  pylint: disable=too-many-arguments
        ctx: typer.Context,
        *,
        profile: Annotated[
            str | None,
            typer.Option("--profile", "-p", envvar="CLOCKIFY_PROFILE", help="Configuration profile to use."),
        ] = None,
        workspace: Annotated[  # pylint: disable=redefined-outer-name
            str | None,
            typer.Option(
                "--workspace", "-w", envvar="CLOCKIFY_WORKSPACE", help="Workspace ID; overrides the profile."
            ),
        ] = None,
        output: Annotated[
            OutputFormat | None,
            typer.Option("--output", "-o", envvar="CLOCKIFY_OUTPUT", case_sensitive=False, help="Output format."),
        ] = None,
        verbose: Annotated[
            bool,
            typer.Option("--verbose", "-v", help="Print HTTP request diagnostics to stderr."),
        ] = False,
        version: Annotated[
            bool,
            typer.Option("--version", callback=print_version, is_eager=True, help="Show the version and exit."),
        ] = False,
    ) -> None:
        del version
        flags = GlobalOptions(profile=profile, workspace=workspace, output=output, verbose=verbose)
        _bind_context(ctx=ctx, services=services_factory(), flags=flags)

    def _bind_context(*, ctx: typer.Context, services: Services, flags: GlobalOptions) -> None:
        resolved = resolve_options(flags, services.settings.load(), is_tty=sys.stdout.isatty())
        console = Console(highlight=False)
        renderer = create_renderer(resolved.output, RenderTarget(console=console, stream=sys.stdout))
        app_context = AppContext(options=resolved, services=services, console=console, renderer=renderer)
        ctx.obj = app_context
        ctx.call_on_close(app_context.close)

    cli.add_typer(auth.APP, name="auth")
    cli.add_typer(config.APP, name="config")
    cli.add_typer(workspace.APP, name="workspace")
    cli.add_typer(user.APP, name="user")
    cli.add_typer(client.APP, name="client")
    cli.add_typer(project.APP, name="project")
    cli.add_typer(tag.APP, name="tag")
    cli.add_typer(task.APP, name="task")
    cli.add_typer(custom_field.APP, name="custom-field")
    cli.add_typer(group.APP, name="group")
    cli.add_typer(entry.APP, name="entry")
    for shortcut in timer_shortcuts.ROOT_COMMANDS:
        cli.command(name=shortcut.__name__.removesuffix("_cmd"), help=shortcut.__doc__ or "")(shortcut)
    return cli


APP: Final = create_app()


def run() -> None:
    APP(prog_name="clockify")
