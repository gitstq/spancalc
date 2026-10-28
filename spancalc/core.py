"""SpanCalc core: human-readable duration parsing, date arithmetic and
epoch conversion. Zero dependencies, standard library only.

Design notes (also the contract the tests pin down):

* A duration is a plain number of seconds (float). Calendar months and
  years have no fixed length, so this library deliberately uses fixed
  approximations and says so in the docs: 1 year = 365 days,
  1 month = 30 days. Calendar-accurate month arithmetic is out of scope;
  business-day arithmetic below is calendar-accurate for weekdays.
* Parsing never uses eval() and never touches the network. Inputs are
  strings, numbers, or files the caller explicitly passes.
* All functions raise ValueError (or TypeError for the wrong type) on
  bad input instead of silently guessing, so the CLI can exit non-zero
  and CI can fail fast.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = [
    "parse_duration",
    "format_duration",
    "breakdown",
    "add_duration",
    "subtract_duration",
    "diff_datetimes",
    "add_business_days",
    "diff_business_days",
    "parse_datetime",
    "to_epoch",
    "from_epoch",
    "weekday_name",
]

# Fixed-length units, in seconds. Month/year are documented approximations.
_UNIT_SECONDS = {
    "y": 365 * 86400.0,
    "year": 365 * 86400.0,
    "years": 365 * 86400.0,
    "mo": 30 * 86400.0,
    "month": 30 * 86400.0,
    "months": 30 * 86400.0,
    "w": 7 * 86400.0,
    "week": 7 * 86400.0,
    "weeks": 7 * 86400.0,
    "d": 86400.0,
    "day": 86400.0,
    "days": 86400.0,
    "h": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
    "hr": 3600.0,
    "hrs": 3600.0,
    "m": 60.0,
    "min": 60.0,
    "mins": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 0.001,
    "millisecond": 0.001,
    "milliseconds": 0.001,
    # Chinese units (no spaces are required between number and unit).
    "年": 365 * 86400.0,
    "月": 30 * 86400.0,
    "周": 7 * 86400.0,
    "天": 86400.0,
    "日": 86400.0,
    "小时": 3600.0,
    "时": 3600.0,
    "分钟": 60.0,
    "分": 60.0,
    "秒": 1.0,
    "毫秒": 0.001,
}

_TOKEN_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+|年|月|周|天|日|小时|时|分钟|分|秒|毫秒)"
)
_ISO_RE = re.compile(
    r"^P(?:(?P<years>\d+(?:\.\d+)?)Y)?(?:(?P<months>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<weeks>\d+(?:\.\d+)?)W)?(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$"
)
_COLON_RE = re.compile(r"^(?P<a>\d+):(?P<b>\d{1,2})(?::(?P<c>\d{1,2}(?:\.\d+)?))?$")

_WEEKDAYS = {
    "zh": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"],
    "zh-TW": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
_DURATION_LABELS = {
    "zh": [("周", 7 * 86400), ("天", 86400), ("小时", 3600), ("分钟", 60), ("秒", 1)],
    "zh-TW": [("週", 7 * 86400), ("天", 86400), ("小時", 3600), ("分鐘", 60), ("秒", 1)],
    "en": [("w", 7 * 86400), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)],
}


def _lookup_unit(unit: str) -> float:
    key = unit.lower()
    if key in _UNIT_SECONDS:
        return _UNIT_SECONDS[key]
    if unit in _UNIT_SECONDS:
        return _UNIT_SECONDS[unit]
    raise ValueError(f"Unknown duration unit: {unit!r}")


def _parse_iso8601(text: str, sign: float) -> float:
    match = _ISO_RE.match(text)
    if not match or not any(match.groupdict().values()):
        raise ValueError(f"Invalid ISO 8601 duration: {text!r}")
    parts = match.groupdict()
    total = 0.0
    for name, seconds in (
        ("years", 365 * 86400.0),
        ("months", 30 * 86400.0),
        ("weeks", 7 * 86400.0),
        ("days", 86400.0),
        ("hours", 3600.0),
        ("minutes", 60.0),
        ("seconds", 1.0),
    ):
        if parts[name] is not None:
            total += float(parts[name]) * seconds
    return sign * total


def _parse_colon(text: str, sign: float) -> float:
    match = _COLON_RE.match(text)
    if not match:
        raise ValueError(f"Invalid duration: {text!r}")
    a, b, c = match.group("a"), match.group("b"), match.group("c")
    if c is not None:
        total = int(a) * 3600 + int(b) * 60 + float(c)
    else:
        total = int(a) * 60 + int(b)
    return sign * total


def parse_duration(value) -> float:
    """Parse a human duration into seconds (float).

    Accepted forms: ``"1w 2d 3h 30m"``, ``"1h30m"``, ``"1.5h"``,
    ``"90m"``, ISO 8601 ``"P2DT3H"`` / ``"PT90M"``, colon ``"1:30:00"``
    (hours:minutes:seconds) or ``"90:00"`` (minutes:seconds), Chinese
    units ``"2天3小时"``, a bare number (seconds), or a leading ``-``
    for a negative duration. ``"0"`` and ``"0s"`` are both valid.
    """
    if isinstance(value, bool):
        raise TypeError("parse_duration() does not accept booleans")
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise TypeError("parse_duration() expects a string or number")
    text = value.strip()
    if not text:
        raise ValueError("Empty duration")
    sign = 1.0
    if text[0] in "+-":
        sign = -1.0 if text[0] == "-" else 1.0
        text = text[1:].strip()
        if not text:
            raise ValueError("Duration has a sign but no value")
    if text.startswith("P") or text.startswith("p"):
        return _parse_iso8601(text.upper(), sign)
    if ":" in text:
        return _parse_colon(text, sign)
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return sign * float(text)
    tokens = _TOKEN_RE.findall(text)
    if not tokens:
        raise ValueError(f"Could not parse duration: {value!r}")
    rebuilt = "".join(f"{n}{u}" for n, u in tokens)
    compact = re.sub(r"\s+", "", text)
    if rebuilt.lower() != compact.lower():
        raise ValueError(f"Could not parse duration: {value!r}")
    return sign * sum(float(n) * _lookup_unit(u) for n, u in tokens)


def breakdown(total_seconds: float) -> dict:
    """Split seconds into weeks/days/hours/minutes/seconds (all ints
    except a possible fractional ``seconds`` remainder)."""
    if not isinstance(total_seconds, (int, float)) or isinstance(total_seconds, bool):
        raise TypeError("breakdown() expects a number")
    sign = -1 if total_seconds < 0 else 1
    remaining = abs(float(total_seconds))
    out = {}
    for name, size in (("weeks", 604800), ("days", 86400), ("hours", 3600), ("minutes", 60)):
        whole, remaining = divmod(remaining, size)
        out[name] = int(whole)
    out["seconds"] = remaining if remaining != int(remaining) else int(remaining)
    out["sign"] = sign
    out["total_seconds"] = float(total_seconds)
    return out


def format_duration(total_seconds: float, lang: str = "zh") -> str:
    """Format seconds as a compact human string, e.g. ``"1周2天3小时"``.

    Zero renders as ``"0秒"`` / ``"0s"``. Negative values keep a leading
    ``-``. Sub-second values render with milliseconds where exact.
    """
    labels = _DURATION_LABELS.get(lang, _DURATION_LABELS["zh"])
    if total_seconds == 0:
        return f"0{labels[-1][0]}"
    sign = "-" if total_seconds < 0 else ""
    remaining = abs(float(total_seconds))
    parts = []
    for label, size in labels:
        whole, remaining = divmod(remaining, size)
        if whole:
            parts.append(f"{int(whole)}{label}")
    if remaining:
        ms = round(remaining * 1000)
        if ms:
            ms_label = "毫秒" if lang in ("zh", "zh-TW") else "ms"
            parts.append(f"{ms}{ms_label}")
    return sign + "".join(parts)


def parse_datetime(value, tz: str | None = None) -> datetime:
    """Parse ``YYYY-MM-DD`` / ``YYYY-MM-DD HH:MM[:SS]`` / ISO 8601 text.

    Naive input is treated as UTC unless ``tz`` (an IANA name such as
    ``"Asia/Shanghai"``) is given. Aware input keeps its own offset and
    ``tz`` must not be passed with it.
    """
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time())
    elif isinstance(value, str):
        text = value.strip()
        try:
            result = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Could not parse datetime: {value!r}") from exc
    else:
        raise TypeError("parse_datetime() expects a string, date or datetime")
    if result.tzinfo is not None:
        if tz is not None:
            raise ValueError("Pass either an aware datetime or tz, not both")
        return result
    if tz is None:
        return result.replace(tzinfo=timezone.utc)
    try:
        return result.replace(tzinfo=ZoneInfo(tz))
    except Exception as exc:
        raise ValueError(f"Unknown timezone: {tz!r}") from exc


def add_duration(start, duration, tz: str | None = None) -> datetime:
    """Return ``start + duration`` (duration parsed by parse_duration)."""
    return parse_datetime(start, tz=tz) + timedelta(seconds=parse_duration(duration))


def subtract_duration(start, duration, tz: str | None = None) -> datetime:
    """Return ``start - duration``."""
    return parse_datetime(start, tz=tz) - timedelta(seconds=parse_duration(duration))


def diff_datetimes(start, end, tz: str | None = None) -> dict:
    """Difference ``end - start`` as seconds, a breakdown and a human string."""
    a, b = parse_datetime(start, tz=tz), parse_datetime(end, tz=tz)
    total = (b - a).total_seconds()
    return {
        "start": a.isoformat(),
        "end": b.isoformat(),
        "total_seconds": total,
        "breakdown": breakdown(total),
        "human_zh": format_duration(total, "zh"),
        "human_en": format_duration(total, "en"),
        "business_days": diff_business_days(a.date(), b.date()),
    }


def _is_business_day(day: date, holidays: frozenset[date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def add_business_days(start, days: int, holidays=None) -> date:
    """Add ``days`` business days to a date, skipping weekends and any
    ``holidays`` (dates or ``YYYY-MM-DD`` strings). Negative ``days``
    walks backwards. The start date itself is never counted."""
    if isinstance(start, datetime):
        current = start.date()
    elif isinstance(start, date):
        current = start
    elif isinstance(start, str):
        current = parse_datetime(start).date()
    else:
        raise TypeError("add_business_days() expects a date, datetime or string")
    if isinstance(days, bool) or not isinstance(days, int):
        raise TypeError("add_business_days() expects an integer day count")
    holiday_set = frozenset(
        parse_datetime(h).date() if isinstance(h, str) else h for h in (holidays or [])
    )
    step = 1 if days >= 0 else -1
    remaining = abs(days)
    while remaining:
        current += timedelta(days=step)
        if _is_business_day(current, holiday_set):
            remaining -= 1
    return current


def diff_business_days(start, end) -> int:
    """Business days in ``(start, end]``; negative when ``end < start``.

    Example: Friday -> Monday is 1 business day, not 3 calendar days.
    """
    a = parse_datetime(start).date() if not isinstance(start, date) else start
    b = parse_datetime(end).date() if not isinstance(end, date) else end
    if isinstance(a, datetime):
        a = a.date()
    if isinstance(b, datetime):
        b = b.date()
    if a == b:
        return 0
    step = 1 if b > a else -1
    count, current = 0, a
    while current != b:
        current += timedelta(days=step)
        if current.weekday() < 5:
            count += step
    return count


def to_epoch(value, tz: str | None = None) -> float:
    """Datetime (or datetime text) -> Unix epoch seconds."""
    return parse_datetime(value, tz=tz).timestamp()


def from_epoch(epoch, tz: str | None = None) -> datetime:
    """Unix epoch seconds -> datetime (UTC by default, or ``tz``)."""
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
        raise TypeError("from_epoch() expects a number")
    zone = ZoneInfo(tz) if tz else timezone.utc
    return datetime.fromtimestamp(float(epoch), tz=zone)


def weekday_name(value, lang: str = "zh") -> str:
    """Weekday name of a date/datetime in ``zh`` / ``zh-TW`` / ``en``."""
    day = parse_datetime(value).date() if not isinstance(value, (date, datetime)) else value
    if isinstance(day, datetime):
        day = day.date()
    return _WEEKDAYS.get(lang, _WEEKDAYS["zh"])[day.weekday()]
