from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Final

if TYPE_CHECKING:
    from collections.abc import Sequence

HTTP_METHODS: Final = frozenset({"get", "post", "put", "patch", "delete"})
ROW_PATTERN: Final = re.compile(r"^\|\s*`(?P<endpoint>[A-Z]+ /[^`]*)`\s*\|.*\|\s*(?P<status>[a-z-]+)\s*\|\s*$")
DONE: Final = "done"


@dataclass(frozen=True, slots=True)
class CoverageReport:
    total: int
    done: int
    missing: tuple[str, ...]
    unknown: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.done == self.total and not self.missing and not self.unknown


def spec_operations(spec: dict[str, object]) -> frozenset[str]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return frozenset()
    operations: set[str] = set()
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method in HTTP_METHODS and isinstance(operation, dict) and not operation.get("deprecated"):
                operations.add(f"{method.upper()} {str(path).removeprefix('/v1')}")
    return frozenset(operations)


def table_statuses(markdown: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in markdown.splitlines():
        match = ROW_PATTERN.match(line)
        if match:
            statuses[match["endpoint"]] = match["status"]
    return statuses


def build_report(operations: frozenset[str], statuses: dict[str, str]) -> CoverageReport:
    return CoverageReport(
        total=len(operations),
        done=sum(1 for endpoint in operations if statuses.get(endpoint) == DONE),
        missing=tuple(sorted(operations - statuses.keys())),
        unknown=tuple(sorted(statuses.keys() - operations)),
    )


def format_report(report: CoverageReport) -> str:
    percent = 100 * report.done / report.total if report.total else 0.0
    lines = [f"CLI coverage: {report.done}/{report.total} operations done ({percent:.0f}%)"]
    lines.extend(f"missing from coverage table: {endpoint}" for endpoint in report.missing)
    lines.extend(f"not in the OpenAPI spec (removed or deprecated upstream?): {row}" for row in report.unknown)
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare docs/coverage.md with Clockify's OpenAPI document.")
    parser.add_argument("--spec", type=Path, default=Path(".cache/openapi.json"))
    parser.add_argument("--coverage", type=Path, default=Path("docs/coverage.md"))
    parser.add_argument("--strict", action="store_true", help="Also fail unless every operation is done.")
    args = parser.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = build_report(spec_operations(spec), table_statuses(args.coverage.read_text(encoding="utf-8")))
    sys.stdout.write(format_report(report))
    if report.missing or report.unknown:
        return 1
    return 0 if report.complete or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
