"""SpanCalc: human-readable duration and date calculation."""

from .core import (
    add_business_days,
    add_duration,
    breakdown,
    diff_business_days,
    diff_datetimes,
    format_duration,
    from_epoch,
    parse_datetime,
    parse_duration,
    subtract_duration,
    to_epoch,
    weekday_name,
)

__version__ = "1.0.0"
__all__ = [
    "add_business_days",
    "add_duration",
    "breakdown",
    "diff_business_days",
    "diff_datetimes",
    "format_duration",
    "from_epoch",
    "parse_datetime",
    "parse_duration",
    "subtract_duration",
    "to_epoch",
    "weekday_name",
    "__version__",
]
