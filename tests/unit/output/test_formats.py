from __future__ import annotations

import io
from typing import Final

from clockify import User
from rich.console import Console

from clockify_unofficial_cli.config.settings import OutputFormat
from clockify_unofficial_cli.output.formats import CsvRenderer
from clockify_unofficial_cli.output.formats import IdRenderer
from clockify_unofficial_cli.output.formats import JsonLinesRenderer
from clockify_unofficial_cli.output.formats import JsonRenderer
from clockify_unofficial_cli.output.formats import TableRenderer
from clockify_unofficial_cli.output.registry import create_renderer
from clockify_unofficial_cli.output.renderer import Column
from clockify_unofficial_cli.output.renderer import RenderTarget
from clockify_unofficial_cli.output.renderer import many
from clockify_unofficial_cli.output.renderer import single
from tests.conftest import USER_PAYLOAD

COLUMNS: Final = (Column("id", "ID"), Column("interval.duration", "Duration"), Column("billable", "Billable"))
RECORDS: Final = (
    {"id": "a1", "interval": {"duration": "PT1H"}, "billable": True, "tags": ["x"]},
    {"id": "b2", "interval": None, "billable": False, "tags": []},
)


def _target() -> tuple[RenderTarget, io.StringIO]:
    stream = io.StringIO()
    console = Console(file=stream, width=120, color_system=None)
    return RenderTarget(console=console, stream=stream), stream


def test_column_reads_dotted_paths_and_tolerates_missing_parents() -> None:
    # Arrange
    column = Column("interval.duration", "Duration")
    # Act
    values = [column.value(record) for record in RECORDS]
    # Assert
    assert values == ["PT1H", None]


def test_many_serializes_models_with_api_field_names() -> None:
    # Arrange
    user = User.model_validate(USER_PAYLOAD)
    # Act
    dataset = many([user], COLUMNS)
    # Assert
    assert dataset.records == [USER_PAYLOAD]
    assert dataset.single is False


def test_json_renderer_prints_object_for_single_record() -> None:
    # Arrange
    target, stream = _target()
    # Act
    JsonRenderer(target).render(single(RECORDS[0], COLUMNS))
    # Assert
    assert stream.getvalue() == (
        '{\n  "id": "a1",\n  "interval": {\n    "duration": "PT1H"\n  },\n'
        '  "billable": true,\n  "tags": [\n    "x"\n  ]\n}\n'
    )


def test_json_lines_renderer_prints_one_record_per_line() -> None:
    # Arrange
    target, stream = _target()
    # Act
    JsonLinesRenderer(target).render(many(RECORDS, COLUMNS))
    # Assert
    assert stream.getvalue().splitlines() == [
        '{"id": "a1", "interval": {"duration": "PT1H"}, "billable": true, "tags": ["x"]}',
        '{"id": "b2", "interval": null, "billable": false, "tags": []}',
    ]


def test_csv_renderer_writes_headers_and_formatted_cells() -> None:
    # Arrange
    target, stream = _target()
    columns = (*COLUMNS, Column("tags", "Tags"))
    # Act
    CsvRenderer(target).render(many(RECORDS, columns))
    # Assert
    assert stream.getvalue() == 'ID,Duration,Billable,Tags\na1,PT1H,yes,"[""x""]"\nb2,,no,[]\n'


def test_id_renderer_prints_only_identifiers() -> None:
    # Arrange
    target, stream = _target()
    # Act
    IdRenderer(target).render(many([*RECORDS, {"name": "no id"}], COLUMNS))
    # Assert
    assert stream.getvalue() == "a1\nb2\n"


def test_table_renderer_lists_rows_under_headers() -> None:
    # Arrange
    target, stream = _target()
    # Act
    TableRenderer(target).render(many(RECORDS, COLUMNS))
    # Assert
    lines = [line for line in stream.getvalue().splitlines() if "a1" in line or "ID" in line]
    assert len(lines) == 2


def test_table_renderer_prints_single_record_as_key_value_pairs() -> None:
    # Arrange
    target, stream = _target()
    # Act
    TableRenderer(target).render(single(RECORDS[0], COLUMNS))
    # Assert
    assert stream.getvalue().split() == ["ID", "a1", "Duration", "PT1H", "Billable", "yes"]


def test_registry_builds_renderer_for_every_format() -> None:
    # Arrange
    target, _ = _target()
    # Act
    renderers = {str(output): type(create_renderer(output, target)).__name__ for output in OutputFormat}
    # Assert
    assert renderers == {
        "table": "TableRenderer",
        "json": "JsonRenderer",
        "jsonl": "JsonLinesRenderer",
        "csv": "CsvRenderer",
        "id": "IdRenderer",
    }
