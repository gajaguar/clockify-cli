import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ApprovalSortOrder
from clockify import ExpenseCategoryCreate
from clockify import ExpenseCategoryFilter
from clockify import ExpenseCategoryStatusUpdate
from clockify import ExpenseCategoryUpdate

from clockify_unofficial_cli.output.columns import EXPENSE_CATEGORIES
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.expenses import find_category
from clockify_unofficial_cli.services.listing import list_from_options

APP: Final = typer.Typer(help="Manage expense categories.", no_args_is_help=True)

_CATEGORY_ARGUMENT: Final = typer.Argument(metavar="CATEGORY", help="Category ID or exact name.")
_UNIT_PRICE: Final = typer.Option("--unit-price", help="Price per unit in major currency units, e.g. 0.58.")


def _cents(unit_price: float) -> int:
    return round(unit_price * 100)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    archived: Annotated[
        bool | None,
        typer.Option("--archived/--no-archived", help="Only archived or only active categories."),
    ] = None
    name: Annotated[str | None, typer.Option("--name", help="Only categories whose name matches.")] = None
    sort_order: Annotated[
        ApprovalSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


@APP.command(name="list", help="List the workspace's expense categories.")
@handle_errors
@options_from(_ListOptions)
def list_categories(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    categories = app_context.workspace().expense_categories
    category_filter = ExpenseCategoryFilter(
        archived=options.archived, name=options.name, sort_order=options.sort_order
    )
    found = list_from_options(
        functools.partial(categories.list, category_filter=category_filter),
        functools.partial(categories.list_page, category_filter=category_filter),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, EXPENSE_CATEGORIES))


@APP.command(help="Create an expense category.")
@handle_errors
def create(
    ctx: typer.Context,
    *,
    name: Annotated[str, typer.Option("--name", help="Category name.")],
    unit: Annotated[str | None, typer.Option("--unit", help="Unit the price applies to, e.g. km.")] = None,
    unit_price: Annotated[float | None, _UNIT_PRICE] = None,
) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    if unit is not None:
        fields["unit"] = unit
    if unit_price is not None:
        fields.update(has_unit_price=True, price_in_cents=_cents(unit_price))
    payload = ExpenseCategoryCreate(name=name, **fields)  # type: ignore[arg-type]
    app_context.render(single(app_context.workspace().expense_categories.create(payload), EXPENSE_CATEGORIES))


@APP.command(help="Update a category; options left out keep their current value.")
@handle_errors
def update(
    ctx: typer.Context,
    term: Annotated[str, _CATEGORY_ARGUMENT],
    *,
    name: Annotated[str | None, typer.Option("--name", help="New name.")] = None,
    unit: Annotated[str | None, typer.Option("--unit", help="New unit.")] = None,
    unit_price: Annotated[float | None, _UNIT_PRICE] = None,
) -> None:
    app_context = get_app_context(ctx)
    current = find_category(app_context, term)
    fields: dict[str, object] = {}
    stored_unit = unit if unit is not None else current.unit
    if stored_unit is not None:
        fields["unit"] = stored_unit
    if unit_price is not None:
        fields.update(has_unit_price=True, price_in_cents=_cents(unit_price))
    elif current.has_unit_price is not None:
        fields["has_unit_price"] = current.has_unit_price
        if current.price_in_cents is not None:
            fields["price_in_cents"] = current.price_in_cents
    payload = ExpenseCategoryUpdate(name=name or current.name or "", **fields)  # type: ignore[arg-type]
    updated = app_context.workspace().expense_categories.update(str(current.id), payload)
    app_context.render(single(updated, EXPENSE_CATEGORIES))


def _set_archived(ctx: typer.Context, term: str, *, archived: bool) -> None:
    app_context = get_app_context(ctx)
    category = find_category(app_context, term)
    payload = ExpenseCategoryStatusUpdate(archived=archived)
    updated = app_context.workspace().expense_categories.update_status(str(category.id), payload)
    app_context.render(single(updated, EXPENSE_CATEGORIES))


@APP.command(help="Archive an expense category.")
@handle_errors
def archive(ctx: typer.Context, term: Annotated[str, _CATEGORY_ARGUMENT]) -> None:
    _set_archived(ctx, term, archived=True)


@APP.command(help="Restore an archived expense category.")
@handle_errors
def restore(ctx: typer.Context, term: Annotated[str, _CATEGORY_ARGUMENT]) -> None:
    _set_archived(ctx, term, archived=False)


@APP.command(help="Delete an expense category.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, _CATEGORY_ARGUMENT],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete expense category '{term}'", assume_yes=yes)
    category = find_category(app_context, term)
    app_context.workspace().expense_categories.delete(str(category.id))
    app_context.notify(f"Deleted expense category '{category.id}'.")
