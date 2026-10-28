"""SpanCalc command line interface.

Exit codes: 0 = success, 2 = bad input (parse error, unknown unit or
timezone). Nothing here writes files or touches the network, so the
tool is safe to run in CI and in shell pipelines.
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import (
    add_business_days,
    add_duration,
    breakdown,
    diff_datetimes,
    format_duration,
    from_epoch,
    parse_datetime,
    parse_duration,
    subtract_duration,
    to_epoch,
    weekday_name,
)
from . import __version__


def _emit(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif isinstance(data, dict) and "human" in data:
        print(data["human"])
    elif isinstance(data, dict) and "result" in data:
        print(data["result"])
    else:
        print(data)


def _holidays(path: str | None):
    if not path:
        return []
    holidays = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                holidays.append(line)
    return holidays


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spancalc",
        description="Human-readable duration and date calculator (zero dependencies).",
    )
    parser.add_argument("--version", action="version", version=f"spancalc {__version__}")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="Parse a duration into seconds.")
    p.add_argument("duration")
    p.add_argument("--lang", default="zh", choices=["zh", "zh-TW", "en"])

    p = sub.add_parser("convert", help="Convert a duration to another unit.")
    p.add_argument("duration")
    p.add_argument("--to", required=True, choices=["weeks", "days", "hours", "minutes", "seconds", "milliseconds"])

    p = sub.add_parser("add", help="Add a duration to a datetime.")
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--duration", required=True)
    p.add_argument("--tz", default=None)

    p = sub.add_parser("sub", help="Subtract a duration from a datetime.")
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--duration", required=True)
    p.add_argument("--tz", default=None)

    p = sub.add_parser("diff", help="Difference between two datetimes.")
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--to", dest="end", required=True)
    p.add_argument("--tz", default=None)
    p.add_argument("--lang", default="zh", choices=["zh", "zh-TW", "en"])

    p = sub.add_parser("epoch", help="Convert between datetimes and Unix epoch seconds.")
    p.add_argument("--from-datetime", dest="from_dt", default=None)
    p.add_argument("--to-datetime", dest="to_dt", type=float, default=None)
    p.add_argument("--tz", default=None)

    p = sub.add_parser("business", help="Add business days to a date.")
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--holidays", default=None, help="File with one YYYY-MM-DD holiday per line.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "parse":
            total = parse_duration(args.duration)
            data = {"duration": args.duration, "total_seconds": total,
                    "breakdown": breakdown(total),
                    "human": format_duration(total, args.lang)}
        elif args.command == "convert":
            total = parse_duration(args.duration)
            factors = {"weeks": 604800.0, "days": 86400.0, "hours": 3600.0,
                       "minutes": 60.0, "seconds": 1.0, "milliseconds": 0.001}
            converted = total / factors[args.to]
            data = {"duration": args.duration, "total_seconds": total,
                    "converted": converted, "unit": args.to,
                    "human": f"{converted:g} {args.to}"}
        elif args.command in ("add", "sub"):
            fn = add_duration if args.command == "add" else subtract_duration
            result = fn(args.start, args.duration, tz=args.tz)
            data = {"start": args.start, "duration": args.duration,
                    "result": result.isoformat(), "epoch": result.timestamp(),
                    "weekday": weekday_name(result),
                    "human": result.isoformat()}
        elif args.command == "diff":
            result = diff_datetimes(args.start, args.end, tz=args.tz)
            result["human"] = format_duration(result["total_seconds"], args.lang)
            data = result
        elif args.command == "epoch":
            if (args.from_dt is None) == (args.to_dt is None):
                raise ValueError("epoch needs exactly one of --from-datetime / --to-datetime")
            if args.from_dt is not None:
                parsed = parse_datetime(args.from_dt, tz=args.tz)
                data = {"datetime": parsed.isoformat(), "epoch": parsed.timestamp(),
                        "weekday": weekday_name(parsed), "human": str(parsed.timestamp())}
            else:
                parsed = from_epoch(args.to_dt, tz=args.tz)
                data = {"epoch": args.to_dt, "datetime": parsed.isoformat(),
                        "weekday": weekday_name(parsed), "human": parsed.isoformat()}
        elif args.command == "business":
            result = add_business_days(args.start, args.days, holidays=_holidays(args.holidays))
            data = {"start": args.start, "days": args.days, "result": result.isoformat(),
                    "weekday": weekday_name(result), "human": result.isoformat()}
        else:  # pragma: no cover - argparse prevents this
            raise ValueError(f"Unknown command: {args.command}")
    except (ValueError, TypeError, OSError) as exc:
        print(f"spancalc: error: {exc}", file=sys.stderr)
        return 2
    _emit(data, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
