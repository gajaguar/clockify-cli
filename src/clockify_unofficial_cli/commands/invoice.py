import functools
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from clockify import ApprovalSortOrder
from clockify import ClientId
from clockify import Invoice
from clockify import InvoiceCreate
from clockify import InvoiceFilter
from clockify import InvoiceFilterContains
from clockify import InvoiceIdFilter
from clockify import InvoiceInfo
from clockify import InvoiceSearch
from clockify import InvoiceSortColumn
from clockify import InvoiceStatus
from clockify import InvoiceStatusUpdate
from clockify import InvoiceTaxType

from clockify_unofficial_cli.commands import invoice_item
from clockify_unofficial_cli.commands import invoice_payment
from clockify_unofficial_cli.commands import invoice_settings
from clockify_unofficial_cli.output.columns import INVOICES
from clockify_unofficial_cli.output.columns import INVOICE_CREATED
from clockify_unofficial_cli.output.columns import INVOICE_DETAILS
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from clockify_unofficial_cli.runtime.context import AppContext
from clockify_unofficial_cli.runtime.context import get_app_context
from clockify_unofficial_cli.runtime.errors import handle_errors
from clockify_unofficial_cli.runtime.params import PagingOptions
from clockify_unofficial_cli.runtime.params import options_from
from clockify_unofficial_cli.runtime.prompts import confirm
from clockify_unofficial_cli.services.files import save_bytes
from clockify_unofficial_cli.services.invoices import InvoiceChanges
from clockify_unofficial_cli.services.invoices import build_invoice_update
from clockify_unofficial_cli.services.listing import list_from_options
from clockify_unofficial_cli.services.money import to_minor_units
from clockify_unofficial_cli.services.parsing import parse_date
from clockify_unofficial_cli.services.parsing import parse_instant
from clockify_unofficial_cli.services.resolve import resolve_client
from clockify_unofficial_cli.services.resolve import resolve_invoice

APP: Final = typer.Typer(help="Manage invoices. Amounts are typed in major units, e.g. 120.50.", no_args_is_help=True)
APP.add_typer(invoice_item.APP, name="item")
APP.add_typer(invoice_payment.APP, name="payment")
APP.add_typer(invoice_settings.APP, name="settings")

_INVOICE_ARGUMENT: Final = typer.Argument(metavar="INVOICE", help="Invoice ID or exact number.")


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    statuses: Annotated[
        list[InvoiceStatus] | None,
        typer.Option("--status", case_sensitive=False, help="UNSENT, SENT, PAID, ...; repeatable."),
    ] = None
    client: Annotated[str | None, typer.Option("--client", help="Only this client (ID or exact name).")] = None
    number: Annotated[str | None, typer.Option("--number", help="Only invoices with this number.")] = None
    issued_from: Annotated[str | None, typer.Option("--issued-from", help="Issued on or after this date.")] = None
    issued_to: Annotated[str | None, typer.Option("--issued-to", help="Issued on or before this date.")] = None
    amount_over: Annotated[float | None, typer.Option("--amount-over", help="Only amounts above this.")] = None
    amount_under: Annotated[float | None, typer.Option("--amount-under", help="Only amounts below this.")] = None
    sort_column: Annotated[
        InvoiceSortColumn | None,
        typer.Option("--sort-column", case_sensitive=False, help="ID, CLIENT, DUE_ON, ISSUE_DATE, AMOUNT or BALANCE."),
    ] = None
    sort_order: Annotated[
        ApprovalSortOrder | None,
        typer.Option("--sort-order", case_sensitive=False, help="ASCENDING or DESCENDING."),
    ] = None


def _search(app_context: AppContext, options: _ListOptions) -> InvoiceSearch | None:
    fields: dict[str, object] = {}
    if options.client:
        ids = [resolve_client(app_context, options.client)]
        fields["clients"] = InvoiceIdFilter(ids=ids, contains=InvoiceFilterContains.CONTAINS)
    if options.number:
        fields["invoice_number"] = options.number
    dates = {
        "issue-date-start": parse_date(options.issued_from) if options.issued_from else None,
        "issue-date-end": parse_date(options.issued_to) if options.issued_to else None,
    }
    given = {name: value for name, value in dates.items() if value is not None}
    if given:
        fields["issue_date"] = given
    if options.amount_over is not None:
        fields["greater_than_amount"] = to_minor_units(options.amount_over)
    if options.amount_under is not None:
        fields["less_than_amount"] = to_minor_units(options.amount_under)
    if not fields:
        return None
    shared = {"statuses": options.statuses, "sort_column": options.sort_column, "sort_order": options.sort_order}
    fields.update({name: value for name, value in shared.items() if value is not None})
    return InvoiceSearch.model_validate(fields)


# Clockify filters by client, number, date and amount through a different endpoint than the plain
# list, so the search endpoint is used only when one of those filters is given.
@APP.command(name="list", help="List invoices, filtered by status, client, number, date or amount.")
@handle_errors
@options_from(_ListOptions)
def list_invoices(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    invoices = app_context.workspace().invoices
    search = _search(app_context, options)
    paging = (options.limit, options.page, options.page_size)
    found: Iterable[Invoice] | Iterable[InvoiceInfo]
    if search is not None:
        found = list_from_options(
            functools.partial(invoices.search, search), functools.partial(invoices.search_page, search), *paging
        )
    else:
        invoice_filter = InvoiceFilter(
            statuses=options.statuses, sort_column=options.sort_column, sort_order=options.sort_order
        )
        found = list_from_options(
            functools.partial(invoices.list, invoice_filter=invoice_filter),
            functools.partial(invoices.list_page, invoice_filter=invoice_filter),
            *paging,
        )
    app_context.render(many(found, INVOICES))


@APP.command(help="Show an invoice by ID or exact number.")
@handle_errors
def get(ctx: typer.Context, term: Annotated[str, _INVOICE_ARGUMENT]) -> None:
    app_context = get_app_context(ctx)
    invoice = app_context.workspace().invoices.get(resolve_invoice(app_context, term))
    app_context.render(single(invoice, INVOICE_DETAILS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    client: Annotated[str, typer.Option("--client", help="Client ID or exact name.")]
    number: Annotated[str, typer.Option("--number", help="Invoice number.")]
    currency: Annotated[str, typer.Option("--currency", help="Currency code, e.g. USD.")]
    due: Annotated[str, typer.Option("--due", help="Due date, e.g. 2026-10-14.")]
    issued: Annotated[str, typer.Option("--issued", help="Issue date.")] = "today"


@APP.command(help="Create an empty invoice for a client.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = InvoiceCreate(
        client_id=ClientId(resolve_client(app_context, options.client)),
        currency=options.currency,
        number=options.number,
        issued_date=parse_instant(options.issued),
        due_date=parse_instant(options.due),
    )
    app_context.render(single(app_context.workspace().invoices.create(payload), INVOICE_CREATED))


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    term: Annotated[str, _INVOICE_ARGUMENT]
    number: Annotated[str | None, typer.Option("--number", help="New invoice number.")] = None
    currency: Annotated[str | None, typer.Option("--currency", help="New currency code.")] = None
    issued: Annotated[str | None, typer.Option("--issued", help="New issue date.")] = None
    due: Annotated[str | None, typer.Option("--due", help="New due date.")] = None
    discount: Annotated[float | None, typer.Option("--discount", help="Discount percentage.")] = None
    tax: Annotated[float | None, typer.Option("--tax", help="Tax percentage.")] = None
    tax2: Annotated[float | None, typer.Option("--tax2", help="Second tax percentage.")] = None
    client: Annotated[str | None, typer.Option("--client", help="New client ID or exact name.")] = None
    company: Annotated[str | None, typer.Option("--company", help="Company ID.")] = None
    note: Annotated[str | None, typer.Option("--note", help="Invoice note.")] = None
    subject: Annotated[str | None, typer.Option("--subject", help="Invoice subject.")] = None
    tax_type: Annotated[
        InvoiceTaxType | None,
        typer.Option("--tax-type", case_sensitive=False, help="COMPOUND, SIMPLE or NONE."),
    ] = None


# Clockify's PUT needs the dates and percentages again, so the stored invoice fills what is left out.
@APP.command(help="Update an invoice; options left out keep their current value.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    invoices = app_context.workspace().invoices
    invoice_id = resolve_invoice(app_context, options.term)
    changes = InvoiceChanges(
        number=options.number,
        currency=options.currency,
        issued_date=parse_instant(options.issued) if options.issued else None,
        due_date=parse_instant(options.due) if options.due else None,
        discount=options.discount,
        tax=options.tax,
        tax2=options.tax2,
        client_id=resolve_client(app_context, options.client) if options.client else None,
        company_id=options.company,
        note=options.note,
        subject=options.subject,
        tax_type=options.tax_type,
    )
    payload = build_invoice_update(invoices.get(invoice_id), changes)
    app_context.render(single(invoices.update(invoice_id, payload), INVOICE_DETAILS))


@APP.command(help="Delete an invoice.")
@handle_errors
def delete(
    ctx: typer.Context,
    term: Annotated[str, _INVOICE_ARGUMENT],
    *,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the interactive confirmation prompt.")] = False,
) -> None:
    app_context = get_app_context(ctx)
    confirm(f"Delete invoice '{term}'", assume_yes=yes)
    invoice_id = resolve_invoice(app_context, term)
    app_context.workspace().invoices.delete(invoice_id)
    app_context.notify(f"Deleted invoice '{invoice_id}'.")


@APP.command(help="Copy an invoice into a new one.")
@handle_errors
def duplicate(ctx: typer.Context, term: Annotated[str, _INVOICE_ARGUMENT]) -> None:
    app_context = get_app_context(ctx)
    copy = app_context.workspace().invoices.duplicate(resolve_invoice(app_context, term))
    app_context.render(single(copy, INVOICE_DETAILS))


@dataclass(frozen=True, slots=True, kw_only=True)
class _ExportOptions:
    term: Annotated[str, _INVOICE_ARGUMENT]
    save: Annotated[str, typer.Option("--save", help="File to write the invoice to, or - for stdout.")]
    locale: Annotated[str, typer.Option("--locale", help="Locale of the exported document, e.g. en or es.")] = "en"
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing file.")] = False


@APP.command(help="Export an invoice as a file; the bytes go to --save, not through -o.")
@handle_errors
@options_from(_ExportOptions)
def export(ctx: typer.Context, options: _ExportOptions) -> None:
    app_context = get_app_context(ctx)
    invoice_id = resolve_invoice(app_context, options.term)
    content = app_context.workspace().invoices.export(invoice_id, user_locale=options.locale)
    app_context.notify(save_bytes(content, options.save, force=options.force))


@APP.command(name="set-status", help="Set an invoice's status, e.g. SENT, PAID or VOID.")
@handle_errors
def set_status(
    ctx: typer.Context,
    term: Annotated[str, _INVOICE_ARGUMENT],
    status: Annotated[InvoiceStatus, typer.Argument(case_sensitive=False, help="The new status.")],
) -> None:
    app_context = get_app_context(ctx)
    invoice_id = resolve_invoice(app_context, term)
    app_context.workspace().invoices.update_status(invoice_id, InvoiceStatusUpdate(invoice_status=status))
    app_context.notify(f"Set invoice '{invoice_id}' to {status}.")
