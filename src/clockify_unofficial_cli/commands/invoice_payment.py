import functools
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import InvoicePaymentCreate

from clockify_unofficial_cli.output.columns import INVOICE_DETAILS
from clockify_unofficial_cli.output.columns import INVOICE_PAYMENTS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.money import to_minor_units
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_invoice

APP: Final = typer.Typer(help="Record and remove invoice payments.", no_args_is_help=True)

_INVOICE_ARGUMENT: Final = typer.Argument(metavar="INVOICE", help="Invoice ID or exact number.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    invoice: Annotated[str, _INVOICE_ARGUMENT]


@APP.command(name="list", help="List the payments of an invoice.")
@handle_errors
@options_from(_ListOptions)
def list_payments(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    payments = app_context.workspace().invoice_payments
    invoice_id = resolve_invoice(app_context, options.invoice)
    found = list_from_options(
        functools.partial(payments.list, invoice_id),
        functools.partial(payments.list_page, invoice_id),
        options.limit,
        options.page,
        options.page_size,
    )
    app_context.render(many(found, INVOICE_PAYMENTS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _AddOptions:
    invoice: Annotated[str, _INVOICE_ARGUMENT]
    amount: Annotated[float, typer.Option("--amount", help="Amount paid, e.g. 120.50.")]
    date: Annotated[str | None, typer.Option("--date", help="When it was paid; defaults to now.")] = None
    note: Annotated[str | None, typer.Option("--note", help="Free-text note.")] = None


# Adding a payment is not retried by Clockify, so repeating the command records it twice.
@APP.command(help="Record a payment against an invoice.")
@handle_errors
@options_from(_AddOptions)
def add(ctx: typer.Context, options: _AddOptions) -> None:
    app_context = get_app_context(ctx)
    fields: dict[str, object] = {}
    if options.date is not None:
        fields["payment_date"] = parse_instant(options.date)
    if options.note is not None:
        fields["note"] = options.note
    payload = InvoicePaymentCreate(amount=to_minor_units(options.amount), **fields)  # type: ignore[arg-type]
    invoice_id = resolve_invoice(app_context, options.invoice)
    app_context.render(single(app_context.workspace().invoice_payments.add(invoice_id, payload), INVOICE_DETAILS))


@APP.command(help="Delete a payment from an invoice.")
@handle_errors
def delete(
    ctx: typer.Context,
    invoice: Annotated[str, _INVOICE_ARGUMENT],
    payment_id: Annotated[str, typer.Argument(metavar="PAYMENT", help="Payment ID.")],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete payment '{payment_id}' of invoice '{invoice}'", assume_yes=yes)
    invoice_id = resolve_invoice(app_context, invoice)
    remaining = app_context.workspace().invoice_payments.delete(invoice_id, payment_id)
    app_context.render(single(remaining, INVOICE_DETAILS))
