from __future__ import annotations

import datetime as dt
import re
from typing import Final

from clockify_unofficial_cli.runtime.errors import CliError
from clockify_unofficial_cli.runtime.exit_codes import ExitCode

_DURATION_PATTERN: Final[str] = r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$"
_DURATION_RE: Final[re.Pattern[str]] = re.compile(_DURATION_PATTERN)

_CLOCK_PATTERN: Final[str] = r"^(\d{1,3}):(\d{2})(?::(\d{2}))?$"
_CLOCK_RE: Final[re.Pattern[str]] = re.compile(_CLOCK_PATTERN)

_RELATIVE_PATTERN: Final[str] = r"^([+-])(\d+)([hm])$"
_RELATIVE_RE: Final[re.Pattern[str]] = re.compile(_RELATIVE_PATTERN)

_DAY_KEYWORDS: Final[frozenset[str]] = frozenset({"today", "tomorrow", "yesterday"})


def parse_duration(value: str) -> dt.timedelta:
    raw = value.strip()
    if not raw:
        message = f"Invalid duration '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if ":" in raw:
        return _parse_clock_duration(raw)
    if _DURATION_RE.match(raw) and any(raw.endswith(unit) for unit in ("h", "m", "s")):
        return _parse_compact_duration(raw)
    message = f"Invalid duration '{value}'."
    raise CliError(message, exit_code=ExitCode.USAGE)


def _parse_compact_duration(value: str) -> dt.timedelta:
    match = _DURATION_RE.match(value)
    if match is None:
        message = f"Invalid duration '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return dt.timedelta(
        hours=int(match.group(1) or 0),
        minutes=int(match.group(2) or 0),
        seconds=int(match.group(3) or 0),
    )


def _parse_clock_duration(value: str) -> dt.timedelta:
    match = _CLOCK_RE.match(value)
    if match is None:
        message = f"Invalid duration '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    hours, minutes, seconds = match.groups()
    return dt.timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds or 0))


def parse_instant(value: str) -> dt.datetime:
    raw = value.strip()
    if not raw:
        message = f"Invalid instant '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if _CLOCK_RE.match(raw):
        return _today_at(raw)
    head, _, tail = raw.partition(" ")
    lowered_head = head.casefold()
    if lowered_head in _DAY_KEYWORDS:
        return _day_keyword_at(lowered_head, tail or "00:00")
    if _RELATIVE_RE.match(raw):
        return _resolve_relative(raw)
    return _resolve_absolute(raw)


def _today_at(time_str: str) -> dt.datetime:
    today = dt.datetime.now(dt.UTC).date()
    hour, minute = _parse_clock(time_str)
    return dt.datetime(today.year, today.month, today.day, hour, minute, tzinfo=dt.UTC)


def _day_keyword_at(keyword: str, time_str: str) -> dt.datetime:
    today = dt.datetime.now(dt.UTC).date()
    if keyword == "today":
        target = today
    elif keyword == "tomorrow":
        target = today + dt.timedelta(days=1)
    else:
        target = today - dt.timedelta(days=1)
    hour, minute = _parse_clock(time_str)
    return dt.datetime(target.year, target.month, target.day, hour, minute, tzinfo=dt.UTC)


def _parse_clock(value: str) -> tuple[int, int]:
    match = _CLOCK_RE.match(value.strip())
    if match is None:
        message = f"Invalid clock time '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    hours, minutes, _ = match.groups()
    return int(hours), int(minutes)


def _resolve_relative(value: str) -> dt.datetime:
    sign, amount, unit = _RELATIVE_RE.match(value).groups()  # type: ignore[union-attr]
    delta = dt.timedelta(hours=int(amount)) if unit == "h" else dt.timedelta(minutes=int(amount))
    if sign == "-":
        delta = -delta
    return dt.datetime.now(dt.UTC) + delta


def _resolve_absolute(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        message = f"Invalid instant '{value}'."
        raise CliError(message, exit_code=ExitCode.USAGE) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def parse_date(value: str) -> dt.date:
    return parse_instant(value).date()


__all__ = ["parse_date", "parse_duration", "parse_instant"]
