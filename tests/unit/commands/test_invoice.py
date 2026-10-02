from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Response

from clockify_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    from pathlib import Path

    import typer
    from typer.testing import CliRunner

WORKSPACE: Final = USER_PAYLOAD["activeWorkspace"]
WS_URL: Final = f"{BASE_URL}/workspaces/{WORKSPACE}"
INVOICES_URL: Final = f"{WS_URL}/invoices"
INVOICE_ID: Final = "a1a1a1a1a1a1a1a1a1a1a1a1"
CLIENT_ID: Final = "b2b2b2b2b2b2b2b2b2b2b2b2"
PROJECT_ID: Final = "c3c3c3c3c3c3c3c3c3c3c3c3"
LISTED: Final = {
    "id": INVOICE_ID,
    "number": "INV-1",
    "status": "SENT",
    "clientName": "Acme",
    "currency": "USD",
    "amount": 12000,
    "balance": 12000,
}
DETAILS: Final = {
    **LISTED,
    "clientId": CLIENT_ID,
    "companyId": "co1",
    "subject": "Web",
    "note": "thanks",
    "issuedDate": "2026-09-01T00:00:00Z",
    "dueDate": "2026-09-30T00:00:00Z",
    "discount": 5.0,
    "tax": 10.0,
    "tax2": 0.0,
    "taxType": "SIMPLE",
}
LABELS: Final = {
    "amount": "Amount",
    "billFrom": "From",
    "billTo": "To",
    "description": "Description",
    "discount": "Discount",
    "dueDate": "Due",
    "issueDate": "Issued",
    "itemType": "Type",
    "notes": "Notes",
    "paid": "Paid",
    "quantity": "Qty",
    "subtotal": "Subtotal",
    "tax": "Tax",
    "tax2": "Tax 2",
    "total": "Total",
    "totalAmount": "Amount due",
    "unitPrice": "Price",
}
SETTINGS: Final = {
    "defaults": {"notes": "Thanks", "subject": "Invoice", "dueDays": 30, "taxPercent": 10.0, "taxType": "SIMPLE"},
    "exportFields": {"itemType": True, "quantity": True, "rtl": False},
    "labels": LABELS,
}


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{WS_URL}/clients").mock(
        return_value=Response(
            200, json=[{"id": CLIENT_ID, "name": "Acme", "workspaceId": WORKSPACE, "archived": False}]
        )
    )
    respx.get(f"{WS_URL}/projects").mock(
        return_value=Response(
            200, json=[{"id": PROJECT_ID, "name": "Website", "workspaceId": WORKSPACE, "archived": False}]
        )
    )


def _listing() -> respx.Route:
    return respx.get(INVOICES_URL).mock(return_value=Response(200, json={"invoices": [LISTED], "total": 1}))


@respx.mock
def test_invoice_list_uses_the_plain_endpoint_without_search_filters(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = _listing()
    # Act
    result = runner.invoke(
        cli,
        ["-o", "json", "invoice", "list", "--status", "SENT", "--sort-column", "AMOUNT", "--sort-order", "ASCENDING"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert dict(route.calls.last.request.url.params) == {
        "statuses": "SENT",
        "sort-column": "AMOUNT",
        "sort-order": "ASCENDING",
        "page": "1",
        "page-size": "200",
    }
    assert [row["id"] for row in json.loads(result.stdout)] == [INVOICE_ID]


@respx.mock
def test_invoice_list_searches_when_a_search_filter_is_given(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{INVOICES_URL}/info").mock(
        return_value=Response(200, json={"invoices": [LISTED], "total": 1})
    )
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "invoice", "list", "--client", "Acme", "--number", "INV-1", "--status", "PAID"),
            *(
                "--issued-from",
                "2026-09-01",
                "--issued-to",
                "2026-09-30",
                "--amount-over",
                "100",
                "--amount-under",
                "500.5",
            ),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "clients": {"ids": [CLIENT_ID], "contains": "CONTAINS"},
        "invoiceNumber": "INV-1",
        "issueDate": {"issue-date-start": "2026-09-01", "issue-date-end": "2026-09-30"},
        "greaterThanAmount": 10000,
        "lessThanAmount": 50050,
        "statuses": ["PAID"],
        "page": 1,
        "pageSize": 200,
    }


@respx.mock
def test_invoice_get_resolves_the_number(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    respx.get(f"{INVOICES_URL}/{INVOICE_ID}").mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(cli, ["-o", "json", "invoice", "get", "INV-1"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["number"] == "INV-1"


@respx.mock
def test_invoice_create_posts_the_dates(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.post(INVOICES_URL).mock(
        return_value=Response(201, json={"id": INVOICE_ID, "number": "INV-2", "clientId": CLIENT_ID})
    )
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "invoice", "create", "--client", "Acme", "--number", "INV-2", "--currency", "USD"),
            *("--issued", "2026-09-01", "--due", "2026-09-30"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "clientId": CLIENT_ID,
        "currency": "USD",
        "number": "INV-2",
        "issuedDate": "2026-09-01T00:00:00Z",
        "dueDate": "2026-09-30T00:00:00Z",
    }


@respx.mock
def test_invoice_update_keeps_what_the_options_leave_out(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _listing()
    item = f"{INVOICES_URL}/{INVOICE_ID}"
    respx.get(item).mock(return_value=Response(200, json=DETAILS))
    route = respx.put(item).mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(cli, ["-o", "json", "invoice", "update", "INV-1", "--number", "INV-9", "--tax", "21"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "currency": "USD",
        "number": "INV-9",
        "issuedDate": "2026-09-01T00:00:00Z",
        "dueDate": "2026-09-30T00:00:00Z",
        "discountPercent": 5.0,
        "taxPercent": 21.0,
        "tax2Percent": 0.0,
        "clientId": CLIENT_ID,
        "companyId": "co1",
        "note": "thanks",
        "subject": "Web",
        "taxType": "SIMPLE",
    }


@respx.mock
def test_invoice_update_needs_a_date_the_invoice_does_not_have(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _listing()
    respx.get(f"{INVOICES_URL}/{INVOICE_ID}").mock(return_value=Response(200, json={**DETAILS, "dueDate": None}))
    # Act
    result = runner.invoke(cli, ["invoice", "update", "INV-1", "--note", "x"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_invoice_update_can_change_every_field(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    item = f"{INVOICES_URL}/{INVOICE_ID}"
    respx.get(item).mock(return_value=Response(200, json=DETAILS))
    route = respx.put(item).mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(
        cli,
        [
            *("invoice", "update", "INV-1", "--currency", "EUR", "--issued", "2026-10-01", "--due", "2026-10-31"),
            *("--discount", "1", "--tax2", "2", "--client", "Acme", "--company", "co2", "--note", "n"),
            *("--subject", "s", "--tax-type", "COMPOUND"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "currency": "EUR",
        "number": "INV-1",
        "issuedDate": "2026-10-01T00:00:00Z",
        "dueDate": "2026-10-31T00:00:00Z",
        "discountPercent": 1.0,
        "taxPercent": 10.0,
        "tax2Percent": 2.0,
        "clientId": CLIENT_ID,
        "companyId": "co2",
        "note": "n",
        "subject": "s",
        "taxType": "COMPOUND",
    }


@respx.mock
def test_invoice_delete_duplicate_and_set_status(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    item = f"{INVOICES_URL}/{INVOICE_ID}"
    delete = respx.delete(item).mock(return_value=Response(204))
    duplicate = respx.post(f"{item}/duplicate").mock(return_value=Response(201, json=DETAILS))
    status = respx.patch(f"{item}/status").mock(return_value=Response(204))
    # Act
    deleted = runner.invoke(cli, ["invoice", "delete", "INV-1", "--yes"])
    copied = runner.invoke(cli, ["-o", "json", "invoice", "duplicate", "INV-1"])
    changed = runner.invoke(cli, ["invoice", "set-status", "INV-1", "PAID"])
    # Assert
    assert (deleted.exit_code, copied.exit_code, changed.exit_code) == (ExitCode.OK, ExitCode.OK, ExitCode.OK)
    assert delete.called
    assert duplicate.called
    assert json.loads(status.calls.last.request.content) == {"invoiceStatus": "PAID"}


@respx.mock
def test_invoice_export_saves_the_file_with_the_locale(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.get(f"{INVOICES_URL}/{INVOICE_ID}/export").mock(return_value=Response(200, content=b"%PDF-invoice"))
    target = tmp_path / "invoice.pdf"
    # Act
    result = runner.invoke(cli, ["invoice", "export", "INV-1", "--save", str(target), "--locale", "es"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert dict(route.calls.last.request.url.params) == {"userLocale": "es"}
    assert target.read_bytes() == b"%PDF-invoice"


@respx.mock
def test_invoice_unknown_number_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    # Act
    result = runner.invoke(cli, ["invoice", "get", "INV-404"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_invoice_item_add_converts_the_price_to_minor_units(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.post(f"{INVOICES_URL}/{INVOICE_ID}/items").mock(return_value=Response(201, json=DETAILS))
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "invoice", "item", "add", "INV-1", "--description", "Design", "--unit-price", "120.50"),
            *("--quantity", "2", "--apply-taxes", "TAX1"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "description": "Design",
        "itemType": "Service",
        "quantity": 2,
        "unitPrice": 12050,
        "applyTaxes": "TAX1",
    }


@respx.mock
def test_invoice_item_import_posts_the_range_and_projects(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.post(f"{INVOICES_URL}/{INVOICE_ID}/items/import").mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "invoice", "item", "import", "INV-1", "--from", "2026-09-01", "--to", "2026-09-30"),
            *("-P", "Website", "--expenses", "--group-type", "DETAILED", "--round-durations"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "from": "2026-09-01T00:00:00Z",
        "to": "2026-09-30T00:00:00Z",
        "importExpenses": True,
        "projectFilter": {"ids": [PROJECT_ID], "contains": "CONTAINS"},
        "timeEntryGroupType": "DETAILED",
        "roundTimeEntryDuration": True,
    }


@respx.mock
def test_invoice_item_import_without_projects_sends_an_empty_filter(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.post(f"{INVOICES_URL}/{INVOICE_ID}/items/import").mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(cli, ["invoice", "item", "import", "INV-1", "--from", "2026-09-01", "--to", "2026-09-30"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "from": "2026-09-01T00:00:00Z",
        "to": "2026-09-30T00:00:00Z",
        "importExpenses": False,
        "projectFilter": {},
        "timeEntryGroupType": "GROUPED",
    }


@respx.mock
def test_invoice_item_delete_by_position(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.delete(f"{INVOICES_URL}/{INVOICE_ID}/items/2").mock(return_value=Response(200, json=DETAILS))
    # Act
    result = runner.invoke(cli, ["invoice", "item", "delete", "INV-1", "2", "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_invoice_payment_list_add_and_delete(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    base = f"{INVOICES_URL}/{INVOICE_ID}/payments"
    listing = respx.get(base).mock(return_value=Response(200, json=[{"id": "p1", "amount": 5000}]))
    add = respx.post(base).mock(return_value=Response(201, json=DETAILS))
    delete = respx.delete(f"{base}/p1").mock(return_value=Response(200, json=DETAILS))
    # Act
    listed = runner.invoke(cli, ["-o", "json", "invoice", "payment", "list", "INV-1"])
    added = runner.invoke(
        cli, ["invoice", "payment", "add", "INV-1", "--amount", "50", "--date", "2026-09-10", "--note", "wire"]
    )
    deleted = runner.invoke(cli, ["invoice", "payment", "delete", "INV-1", "p1", "--yes"])
    # Assert
    assert (listed.exit_code, added.exit_code, deleted.exit_code) == (ExitCode.OK, ExitCode.OK, ExitCode.OK)
    assert dict(listing.calls.last.request.url.params) == {"page": "1", "page-size": "200"}
    assert json.loads(add.calls.last.request.content) == {
        "amount": 5000,
        "paymentDate": "2026-09-10T00:00:00Z",
        "note": "wire",
    }
    assert delete.called


@respx.mock
def test_invoice_payment_add_with_only_an_amount(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    _listing()
    route = respx.post(f"{INVOICES_URL}/{INVOICE_ID}/payments").mock(return_value=Response(201, json=DETAILS))
    # Act
    result = runner.invoke(cli, ["invoice", "payment", "add", "INV-1", "--amount", "0.1"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {"amount": 10}


@respx.mock
def test_invoice_settings_get(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{INVOICES_URL}/settings").mock(return_value=Response(200, json=SETTINGS))
    # Act
    result = runner.invoke(cli, ["-o", "json", "invoice", "settings", "get"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["defaults"]["subject"] == "Invoice"


@respx.mock
def test_invoice_settings_update_sends_back_every_label(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{INVOICES_URL}/settings").mock(return_value=Response(200, json=SETTINGS))
    route = respx.put(f"{INVOICES_URL}/settings").mock(return_value=Response(200, json=SETTINGS))
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "invoice", "settings", "update", "--subject", "Bill", "--due-days", "15"),
            *("--label", "due_date=Pay by", "--hide", "quantity", "--show", "rtl"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "labels": {
            "amount": "Amount",
            "billFrom": "From",
            "billTo": "To",
            "description": "Description",
            "discount": "Discount",
            "dueDate": "Pay by",
            "issueDate": "Issued",
            "itemType": "Type",
            "notes": "Notes",
            "paid": "Paid",
            "quantity": "Qty",
            "subtotal": "Subtotal",
            "tax": "Tax",
            "tax2": "Tax 2",
            "total": "Total",
            "totalAmountDue": "Amount due",
            "unitPrice": "Price",
        },
        "defaults": {
            "notes": "Thanks",
            "subject": "Bill",
            "dueDays": 15,
            "taxPercent": 10.0,
            "taxType": "SIMPLE",
        },
        "exportFields": {"itemType": True, "quantity": False, "rtl": True},
    }


@respx.mock
def test_invoice_settings_update_rejects_unknown_label_and_field(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{INVOICES_URL}/settings").mock(return_value=Response(200, json=SETTINGS))
    # Act
    bad_label = runner.invoke(cli, ["invoice", "settings", "update", "--label", "colour=red"])
    bad_field = runner.invoke(cli, ["invoice", "settings", "update", "--show", "logo"])
    # Assert
    assert (bad_label.exit_code, bad_field.exit_code) == (ExitCode.USAGE, ExitCode.USAGE)


@respx.mock
def test_invoice_settings_update_needs_the_stored_labels(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{INVOICES_URL}/settings").mock(return_value=Response(200, json={"defaults": {"notes": "n"}}))
    # Act
    result = runner.invoke(cli, ["invoice", "settings", "update", "--notes", "x"])
    # Assert
    assert result.exit_code == ExitCode.USAGE
