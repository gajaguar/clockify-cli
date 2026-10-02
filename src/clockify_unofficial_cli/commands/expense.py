import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer
from clockify import ExpenseCategoryId
from clockify import ExpenseCreate
from clockify import ProjectId
from clockify import TaskId
from clockify import UserId

from clockify_unofficial_cli.commands import expense_category
from clockify_unofficial_cli.output.columns import EXPENSE
from clockify_unofficial_cli.output.columns import EXPENSES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.expenses import ExpenseChanges
from clockify_unofficial_cli.services.expenses import build_update
from clockify_unofficial_cli.services.expenses import read_receipt
from clockify_unofficial_cli.services.files import save_bytes
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_expense_category
from clockify_unofficial_cli.services.resolve import resolve_project
from clockify_unofficial_cli.services.resolve import resolve_task
from clockify_unofficial_cli.services.resolve import resolve_user

APP: Final = typer.Typer(help="Manage expenses and their receipts.", no_args_is_help=True)
APP.add_typer(expense_category.APP, name="category")

_EXPENSE_ARGUMENT: Final = typer.Argument(metavar="EXPENSE", help="Expense ID.")
_RECEIPT_OPTION: Final = typer.Option(
    "--receipt", exists=True, dir_okay=False, readable=True, help="Receipt file to upload."
)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    user: Annotated[str | None, typer.Option("--user", help="Only this user's expenses (ID, email or name).")] = None


@APP.command(name="list", help="List expenses.")
@handle_errors
@options_from(_ListOptions)
def list_expenses(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    expenses = app_context.workspace().expenses
    user_id = resolve_user(app_context, options.user) if options.user else None
    found = list_from_options(
        functools.partial(expenses.list, user_id=user_id),
        functools.partial(expenses.list_page, user_id=user_id),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, EXPENSES))


@APP.command(help="Show an expense by ID.")
@handle_errors
def get(ctx: typer.Context, expense_id: Annotated[str, _EXPENSE_ARGUMENT]) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.workspace().expenses.get(expense_id), EXPENSE))


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    category: Annotated[str, typer.Option("--category", help="Category ID or exact name.")]
    project: Annotated[str, typer.Option("--project", "-P", help="Project ID or exact name.")]
    amount: Annotated[float, typer.Option("--amount", help="Total amount, or units when the category has a price.")]
    date: Annotated[str, typer.Option("--date", help="When it happened, e.g. 2026-09-14 or yesterday.")] = "today"
    task: Annotated[str | None, typer.Option("--task", "-t", help="Task ID or exact name in the project.")] = None
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--non-billable", help="Whether the expense is billable."),
    ] = None
    notes: Annotated[str | None, typer.Option("--notes", help="Free-text notes.")] = None
    receipt: Annotated[Path | None, _RECEIPT_OPTION] = None
    user: Annotated[str | None, typer.Option("--user", help="Owner; defaults to you.")] = None


@APP.command(help="Create an expense, optionally with a receipt file.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    project_id = resolve_project(app_context, options.project)
    fields: dict[str, object] = {}
    if options.task is not None:
        fields["task_id"] = TaskId(resolve_task(app_context, ProjectId(project_id), options.task))
    if options.billable is not None:
        fields["billable"] = options.billable
    if options.notes is not None:
        fields["notes"] = options.notes
    if options.receipt is not None:
        fields["file"] = read_receipt(options.receipt)
    payload = ExpenseCreate(
        user_id=UserId(resolve_user(app_context, options.user)) if options.user else app_context.user_id(),
        category_id=ExpenseCategoryId(resolve_expense_category(app_context, options.category)),
        project_id=ProjectId(project_id),
        date=parse_instant(options.date),
        amount=options.amount,
        **fields,  # type: ignore[arg-type]
    )
    app_context.render(single(app_context.workspace().expenses.create(payload), EXPENSE))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    expense_id: Annotated[str, _EXPENSE_ARGUMENT]
    category: Annotated[str | None, typer.Option("--category", help="New category ID or exact name.")] = None
    project: Annotated[str | None, typer.Option("--project", "-P", help="New project ID or exact name.")] = None
    task: Annotated[str | None, typer.Option("--task", "-t", help="New task ID or exact name.")] = None
    date: Annotated[str | None, typer.Option("--date", help="New date.")] = None
    amount: Annotated[float | None, typer.Option("--amount", help="New amount.")] = None
    billable: Annotated[
        bool | None,
        typer.Option("--billable/--non-billable", help="Whether the expense is billable."),
    ] = None
    notes: Annotated[str | None, typer.Option("--notes", help="New notes.")] = None
    receipt: Annotated[Path | None, _RECEIPT_OPTION] = None


@APP.command(help="Update an expense; only the options you pass are changed.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    expenses = app_context.workspace().expenses
    current = expenses.get(options.expense_id)
    new_project_id = resolve_project(app_context, options.project) if options.project else None
    task_project_id = new_project_id or (str(current.project_id) if current.project_id else None)
    task_id = None
    if options.task:
        if task_project_id is None:
            message = "--task needs a project; pass --project."
            raise CliError(message, exit_code=ExitCode.USAGE)
        task_id = resolve_task(app_context, ProjectId(task_project_id), options.task)
    changes = ExpenseChanges(
        category_id=resolve_expense_category(app_context, options.category) if options.category else None,
        project_id=new_project_id,
        task_id=task_id,
        date=options.date,
        amount=options.amount,
        billable=options.billable,
        notes=options.notes,
        receipt=read_receipt(options.receipt) if options.receipt else None,
    )
    updated = expenses.update(options.expense_id, build_update(current, changes))
    app_context.render(single(updated, EXPENSE))


@APP.command(help="Delete an expense.")
@handle_errors
def delete(
    ctx: typer.Context,
    expense_id: Annotated[str, _EXPENSE_ARGUMENT],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete expense '{expense_id}'", assume_yes=yes)
    app_context.workspace().expenses.delete(expense_id)
    app_context.notify(f"Deleted expense '{expense_id}'.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ReceiptOptions:
    expense_id: Annotated[str, _EXPENSE_ARGUMENT]
    save: Annotated[str, typer.Option("--save", help="File to write the receipt to, or - for stdout.")]
    file_id: Annotated[
        str | None, typer.Option("--file-id", help="Receipt ID; defaults to the expense's receipt.")
    ] = None
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing file.")] = False


@APP.command(help="Download an expense's receipt; the bytes go to --save, not through -o.")
@handle_errors
@options_from(_ReceiptOptions)
def receipt(ctx: typer.Context, options: _ReceiptOptions) -> None:
    app_context = get_app_context(ctx)
    expenses = app_context.workspace().expenses
    file_id = options.file_id or expenses.get(options.expense_id).file_id
    if file_id is None:
        message = f"Expense '{options.expense_id}' has no receipt."
        raise CliError(message, exit_code=ExitCode.NOT_FOUND)
    content = expenses.download_file(options.expense_id, file_id)
    app_context.notify(save_bytes(content, options.save, force=options.force))
