# SpanCalc design notes

## Problem

Shell scripts, CI jobs, and data pipelines constantly need small time
arithmetic — "90 minutes from now", "how long between these two
timestamps", "the next business day" — but the usual answers are a
one-off `date` incantation, a spreadsheet, or a dependency that drags
in a whole date library. SpanCalc is the boring, dependable middle:
one zero-dependency Python package that answers those questions the
same way on every machine.

## What SpanCalc is not

- Not a time tracker. It never records, stores, or times anything.
  (Time tracking, Pomodoro, and productivity analytics belong to
  other tools; SpanCalc only calculates.)
- Not a scheduler. It does not run jobs or send reminders.
- Not a calendar library. Month and year are fixed approximations
  (30 / 365 days), stated openly, because a duration string such as
  "1mo" has no single calendar meaning. Business-day arithmetic, by
  contrast, is calendar-accurate for weekdays and explicit holidays.

## Architecture

```text
spancalc/
  core.py    # pure functions: parse, format, add, diff, business days, epoch
  cli.py     # argparse front end; translates results to text or JSON
  __init__.py  # public API surface
tests/
  test_spancalc.py  # 39 tests: parsing, formatting, dates, business days, CLI
```

`core.py` has no I/O and no global state, so it is usable as a library
and trivial to test. `cli.py` owns all I/O: it reads an optional
holidays file, prints text or JSON, and maps bad input to exit code 2.

## Key decisions

1. **Seconds as the canonical unit.** Every duration becomes a float
   number of seconds; every other representation is a view of it.
2. **Fail loudly.** Unknown units, garbage input, and unknown
   timezones raise `ValueError` instead of being guessed, so scripts
   and CI fail fast rather than silently computing the wrong date.
3. **Weekdays first, holidays explicit.** Business days skip Saturday
   and Sunday by default; holidays come only from a file the user
   passes, never from a hidden built-in list that would go stale.
4. **Naive input means UTC.** A datetime without an offset is UTC
   unless `--tz` names an IANA timezone, so the same command gives the
   same answer everywhere.

## Iteration plan

- v1.1: relative expressions ("next Monday", "end of month") as a
  separate, well-tested parser — only if they stay unambiguous.
- v1.2: `--from-stdin` batch mode for processing many durations or
  datetimes in one invocation.
- v1.3: optional holiday calendars shipped as data files (still
  explicit, still offline), per region.
