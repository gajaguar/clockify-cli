from typing import Annotated
from typing import Final

import typer

from clockify_unofficial_cli.output.columns import WORKSPACES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.output.renderer import to_record
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.services.resolve import Candidate
from clockify_unofficial_cli.services.resolve import resolve

APP: Final = typer.Typer(help="Inspect and select the Clockify workspace.", no_args_is_help=True)


@APP.command(name="list", help="List every workspace the API key can see.")
@handle_errors
def list_workspaces(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    workspaces = app_context.client().workspaces.list()
    app_context.render(many(workspaces, WORKSPACES))


@APP.command(help="Show a workspace by ID or name; defaults to the active one.")
@handle_errors
def get(
    ctx: typer.Context,
    workspace_id: Annotated[
        str | None,
        typer.Argument(help="Workspace ID or exact name; defaults to the resolved workspace."),
    ] = None,
) -> None:
    app_context = get_app_context(ctx)
    if workspace_id is None:
        workspace = app_context.workspace()
        app_context.render(single({"id": str(workspace.id), "name": "<active workspace>"}, WORKSPACES))
        return
    workspaces = app_context.client().workspaces.list()
    candidates = [Candidate(id=str(item.id), name=item.name) for item in workspaces]
    resolved_id = resolve(workspace_id, candidates, noun="workspace")
    record: dict[str, object] = dict(next(to_record(item) for item in workspaces if str(item.id) == resolved_id))
    app_context.render(single(record, WORKSPACES))


@APP.command(help="Persist the workspace choice in the active profile.")
@handle_errors
def use(
    ctx: typer.Context,
    workspace_id: Annotated[str, typer.Argument(help="Workspace ID or exact name to make the default.")],
) -> None:
    app_context = get_app_context(ctx)
    workspaces = app_context.client().workspaces.list()
    candidates = [Candidate(id=str(item.id), name=item.name) for item in workspaces]
    resolved_id = resolve(workspace_id, candidates, noun="workspace")
    store = app_context.services.settings
    settings = store.load()
    options = app_context.options
    if options.profile_name not in settings.profiles:
        message = f"No profile named '{options.profile_name}'; run `clockify auth login`."
        raise CliError(message, exit_code=ExitCode.CONFIGURATION)
    profile = settings.profiles[options.profile_name]
    updated = profile.model_copy(update={"workspace_id": resolved_id})
    store.save(settings.with_profile(options.profile_name, updated))
    app_context.notify(f"Workspace set to '{resolved_id}' for profile '{options.profile_name}'.")
