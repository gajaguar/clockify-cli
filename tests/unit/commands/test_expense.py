from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from typing import Final

import respx
from httpx import Request
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
EXPENSE_ID: Final = "343434343434343434343434"
CATEGORY_ID: Final = "565656565656565656565656"
PROJECT_ID: Final = "787878787878787878787878"
TASK_ID: Final = "909090909090909090909090"
RECEIPT_ID: Final = "ab12ab12ab12ab12ab12ab12"
EXPENSE: Final = {
    "id": EXPENSE_ID,
    "workspaceId": WORKSPACE,
    "userId": USER_PAYLOAD["id"],
    "categoryId": CATEGORY_ID,
    "projectId": PROJECT_ID,
    "date": "2026-09-14T00:00:00Z",
    "total": 12.5,
    "billable": False,
    "notes": "taxi",
    "fileId": RECEIPT_ID,
}
DETAILS: Final = {
    "id": EXPENSE_ID,
    "category": {"id": CATEGORY_ID, "name": "Travel"},
    "project": {"id": PROJECT_ID, "name": "Website"},
    "date": "2026-09-14T00:00:00Z",
    "total": 12.5,
    "fileName": "taxi.pdf",
}
CATEGORY: Final = {"id": CATEGORY_ID, "workspaceId": WORKSPACE, "name": "Travel", "archived": False}
PROJECT: Final = {"id": PROJECT_ID, "name": "Website", "workspaceId": WORKSPACE, "archived": False}
TASK: Final = {"id": TASK_ID, "name": "Design", "projectId": PROJECT_ID, "status": "ACTIVE"}


def _login(environ: dict[str, str]) -> None:
    environ["CLOCKIFY_API_KEY"] = "secret"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json=USER_PAYLOAD))
    respx.get(f"{WS_URL}/users").mock(return_value=Response(200, json=[USER_PAYLOAD]))
    respx.get(f"{WS_URL}/projects").mock(return_value=Response(200, json=[PROJECT]))
    respx.get(f"{WS_URL}/projects/{PROJECT_ID}/tasks").mock(return_value=Response(200, json=[TASK]))
    respx.get(f"{WS_URL}/expenses/categories").mock(
        return_value=Response(200, json={"categories": [CATEGORY], "count": 1})
    )


def _form(request: Request) -> dict[str, str]:
    boundary = request.headers["content-type"].split("boundary=")[1].encode()
    fields: dict[str, list[str]] = {}
    for part in request.content.split(b"--" + boundary):
        head, _, body = part.strip(b"\r\n").partition(b"\r\n\r\n")
        found = re.search(rb'name="([^"]+)"', head)
        if found is not None:
            fields.setdefault(found.group(1).decode(), []).append(body.decode(errors="replace"))
    return {name: ",".join(values) for name, values in fields.items()}


@respx.mock
def test_expense_list_filters_by_user(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.get(f"{WS_URL}/expenses").mock(
        return_value=Response(200, json={"expenses": {"expenses": [DETAILS], "count": 1}})
    )
    # Act
    result = runner.invoke(cli, ["-o", "json", "expense", "list", "--user", USER_PAYLOAD["id"]])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert dict(route.calls.last.request.url.params) == {
        "user-id": USER_PAYLOAD["id"],
        "page": "1",
        "page-size": "200",
    }
    assert [row["id"] for row in json.loads(result.stdout)] == [EXPENSE_ID]


@respx.mock
def test_expense_get_renders_the_expense(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(200, json=EXPENSE))
    # Act
    result = runner.invoke(cli, ["-o", "json", "expense", "get", EXPENSE_ID])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["id"] == EXPENSE_ID


@respx.mock
def test_expense_create_uploads_a_multipart_form_with_the_receipt(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    receipt = tmp_path / "taxi.pdf"
    receipt.write_bytes(b"%PDF-receipt")
    route = respx.post(f"{WS_URL}/expenses").mock(return_value=Response(201, json=EXPENSE))
    # Act
    result = runner.invoke(
        cli,
        [
            *("-o", "json", "expense", "create", "--category", "Travel", "-P", "Website", "--amount", "12.5"),
            *("--date", "2026-09-14", "--task", "Design", "--billable", "--notes", "taxi", "--receipt", str(receipt)),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert _form(request) == {
        "userId": USER_PAYLOAD["id"],
        "categoryId": CATEGORY_ID,
        "projectId": PROJECT_ID,
        "date": "2026-09-14T00:00:00Z",
        "amount": "12.5",
        "taskId": TASK_ID,
        "billable": "true",
        "notes": "taxi",
        "file": "%PDF-receipt",
    }


@respx.mock
def test_expense_create_for_another_user_without_a_receipt(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{WS_URL}/expenses").mock(return_value=Response(201, json=EXPENSE))
    # Act
    result = runner.invoke(
        cli,
        [
            "expense",
            "create",
            "--category",
            CATEGORY_ID,
            "-P",
            PROJECT_ID,
            "--amount",
            "3",
            "--user",
            "someone@example.com",
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert _form(route.calls.last.request) == {
        "userId": USER_PAYLOAD["id"],
        "categoryId": CATEGORY_ID,
        "projectId": PROJECT_ID,
        "date": _form(route.calls.last.request)["date"],
        "amount": "3.0",
    }


@respx.mock
def test_expense_create_rejects_a_missing_receipt_file(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    missing = tmp_path / "nope.pdf"
    # Act
    result = runner.invoke(
        cli,
        ["expense", "create", "--category", "Travel", "-P", "Website", "--amount", "1", "--receipt", str(missing)],
    )
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_expense_update_sends_only_the_changed_fields(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    item = f"{WS_URL}/expenses/{EXPENSE_ID}"
    respx.get(item).mock(return_value=Response(200, json=EXPENSE))
    route = respx.put(item).mock(return_value=Response(200, json=EXPENSE))
    # Act
    result = runner.invoke(cli, ["-o", "json", "expense", "update", EXPENSE_ID, "--amount", "20", "--task", "Design"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert _form(route.calls.last.request) == {
        "userId": USER_PAYLOAD["id"],
        "categoryId": CATEGORY_ID,
        "date": "2026-09-14T00:00:00Z",
        "amount": "20.0",
        "changeFields": "TASK,AMOUNT",
        "projectId": PROJECT_ID,
        "taskId": TASK_ID,
        "billable": "false",
        "notes": "taxi",
    }


@respx.mock
def test_expense_update_needs_something_to_change(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(200, json=EXPENSE))
    # Act
    result = runner.invoke(cli, ["expense", "update", EXPENSE_ID])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_expense_update_task_needs_a_project(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(200, json={**EXPENSE, "projectId": None}))
    # Act
    result = runner.invoke(cli, ["expense", "update", EXPENSE_ID, "--task", "Design"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_expense_update_with_a_new_receipt_and_category(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    receipt = tmp_path / "new.png"
    receipt.write_bytes(b"png")
    item = f"{WS_URL}/expenses/{EXPENSE_ID}"
    respx.get(item).mock(return_value=Response(200, json=EXPENSE))
    route = respx.put(item).mock(return_value=Response(200, json=EXPENSE))
    # Act
    result = runner.invoke(
        cli,
        [
            *("expense", "update", EXPENSE_ID, "--category", "Travel", "-P", "Website", "--receipt", str(receipt)),
            *("--non-billable", "--date", "2026-09-15", "--notes", "new"),
        ],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert _form(route.calls.last.request)["changeFields"] == "CATEGORY,PROJECT,DATE,BILLABLE,NOTES,FILE"


@respx.mock
def test_expense_delete_with_yes(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.delete(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(204))
    # Act
    result = runner.invoke(cli, ["expense", "delete", EXPENSE_ID, "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_expense_receipt_saves_the_bytes_to_a_file(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(200, json=EXPENSE))
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}/files/{RECEIPT_ID}").mock(return_value=Response(200, content=b"%PDF-1"))
    target = tmp_path / "out.pdf"
    # Act
    result = runner.invoke(cli, ["expense", "receipt", EXPENSE_ID, "--save", str(target)])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert target.read_bytes() == b"%PDF-1"


@respx.mock
def test_expense_receipt_refuses_to_overwrite_without_force(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}/files/{RECEIPT_ID}").mock(return_value=Response(200, content=b"new"))
    target = tmp_path / "out.pdf"
    target.write_bytes(b"old")
    # Act
    refused = runner.invoke(cli, ["expense", "receipt", EXPENSE_ID, "--file-id", RECEIPT_ID, "--save", str(target)])
    forced = runner.invoke(
        cli, ["expense", "receipt", EXPENSE_ID, "--file-id", RECEIPT_ID, "--save", str(target), "--force"]
    )
    # Assert
    assert (refused.exit_code, forced.exit_code) == (ExitCode.USAGE, ExitCode.OK)
    assert target.read_bytes() == b"new"


@respx.mock
def test_expense_receipt_streams_to_stdout_when_asked(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}/files/{RECEIPT_ID}").mock(
        return_value=Response(200, content=b"\x00\x01")
    )
    # Act
    result = runner.invoke(cli, ["expense", "receipt", EXPENSE_ID, "--file-id", RECEIPT_ID, "--save", "-"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert result.stdout_bytes == b"\x00\x01"


@respx.mock
def test_expense_receipt_without_a_receipt_is_not_found(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}").mock(return_value=Response(200, json={**EXPENSE, "fileId": None}))
    # Act
    result = runner.invoke(cli, ["expense", "receipt", EXPENSE_ID, "--save", str(tmp_path / "x")])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_expense_receipt_reports_a_destination_that_cannot_be_written(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    _login(environ)
    respx.get(f"{WS_URL}/expenses/{EXPENSE_ID}/files/{RECEIPT_ID}").mock(return_value=Response(200, content=b"x"))
    target = tmp_path / "missing-dir" / "out.pdf"
    # Act
    result = runner.invoke(cli, ["expense", "receipt", EXPENSE_ID, "--file-id", RECEIPT_ID, "--save", str(target)])
    # Assert
    assert result.exit_code == ExitCode.FAILURE


@respx.mock
def test_category_list_sends_the_filters(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["-o", "json", "expense", "category", "list", "--no-archived", "--name", "Tra"])
    # Assert
    assert result.exit_code == ExitCode.OK
    params = dict(respx.calls.last.request.url.params)
    assert params == {"archived": "false", "name": "Tra", "page": "1", "page-size": "200"}


@respx.mock
def test_category_create_converts_the_unit_price_to_cents(
    runner: CliRunner, cli: typer.Typer, environ: dict[str, str]
) -> None:
    # Arrange
    _login(environ)
    route = respx.post(f"{WS_URL}/expenses/categories").mock(return_value=Response(201, json=CATEGORY))
    # Act
    result = runner.invoke(
        cli, ["expense", "category", "create", "--name", "Mileage", "--unit", "km", "--unit-price", "0.58"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "name": "Mileage",
        "unit": "km",
        "hasUnitPrice": True,
        "priceInCents": 58,
    }


@respx.mock
def test_category_update_keeps_the_stored_price(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    priced = {**CATEGORY, "unit": "km", "hasUnitPrice": True, "priceInCents": 58}
    respx.get(f"{WS_URL}/expenses/categories").mock(return_value=Response(200, json={"categories": [priced]}))
    route = respx.put(f"{WS_URL}/expenses/categories/{CATEGORY_ID}").mock(return_value=Response(200, json=priced))
    # Act
    result = runner.invoke(cli, ["expense", "category", "update", "Travel", "--name", "Trips"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "name": "Trips",
        "unit": "km",
        "hasUnitPrice": True,
        "priceInCents": 58,
    }


@respx.mock
def test_category_update_can_set_a_new_price(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    route = respx.put(f"{WS_URL}/expenses/categories/{CATEGORY_ID}").mock(return_value=Response(200, json=CATEGORY))
    # Act
    result = runner.invoke(cli, ["expense", "category", "update", "Travel", "--unit", "mi", "--unit-price", "1.2"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(route.calls.last.request.content) == {
        "name": "Travel",
        "unit": "mi",
        "hasUnitPrice": True,
        "priceInCents": 120,
    }


@respx.mock
def test_category_archive_restore_and_delete(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    status = respx.patch(f"{WS_URL}/expenses/categories/{CATEGORY_ID}/status").mock(
        return_value=Response(200, json=CATEGORY)
    )
    delete = respx.delete(f"{WS_URL}/expenses/categories/{CATEGORY_ID}").mock(return_value=Response(204))
    # Act
    archived = runner.invoke(cli, ["expense", "category", "archive", "Travel"])
    restored = runner.invoke(cli, ["expense", "category", "restore", "Travel"])
    deleted = runner.invoke(cli, ["expense", "category", "delete", "Travel", "--yes"])
    # Assert
    assert (archived.exit_code, restored.exit_code, deleted.exit_code) == (ExitCode.OK, ExitCode.OK, ExitCode.OK)
    assert [json.loads(call.request.content) for call in status.calls] == [{"archived": True}, {"archived": False}]
    assert delete.called


@respx.mock
def test_category_unknown_name_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["expense", "category", "archive", "Nope"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND


@respx.mock
def test_category_unlisted_id_is_not_found(runner: CliRunner, cli: typer.Typer, environ: dict[str, str]) -> None:
    # Arrange
    _login(environ)
    # Act
    result = runner.invoke(cli, ["expense", "category", "archive", "ffffffffffffffffffffffff"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND
