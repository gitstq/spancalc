# SpanCalc test report — 2026-10-28

## How to run

```bash
python -m unittest discover -s tests -v
```

## Result

39 tests, all passing (final run: `Ran 39 tests ... OK`).

Coverage by area:

- Duration parsing (13 tests): mixed units, concatenated units,
  fractional values, bare numbers, negative durations, ISO 8601,
  colon form, Chinese units, zero, unknown units, garbage input,
  boolean rejection.
- Formatting and breakdown (6 tests): weeks/days/hours/minutes
  breakdown, zh / zh-TW / en formatting, zero and negative values,
  parse-format round-trip.
- Dates and epochs (8 tests): add/subtract with timezone, diff
  (including negative), epoch round-trip, weekday names, bad datetime
  and bad timezone rejection.
- Business days (5 tests): Friday to Monday, weekend skipping,
  negative counts, explicit holidays, business-day diff in both
  directions and the zero case.
- CLI (7 tests): parse, JSON parse, add, diff, business, epoch, and
  exit code 2 on bad input.

## One fix found by the tests

The first run failed 3 tests because the test expectations themselves
had a wrong total: 1 week + 2 days + 3 hours + 30 minutes is
790200 seconds, not 788400. The implementation was correct; the test
expectations were corrected and the suite now passes. No production
code was changed to make the tests pass.

## Manual CLI checks (also passing)

- `parse "1w 2d 3h 30m"` -> `1周2天3小时30分钟`
- `add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Shanghai`
  -> `2026-10-30T13:00:00+08:00`
- `business --from "2026-10-30" --days 1` -> `2026-11-02`
- `epoch --to-datetime 0 --tz Asia/Shanghai` -> `1970-01-01T08:00:00+08:00`
- `parse "3 parsecs"` -> error on stderr, exit code 2

## Security note

No network access, no eval(), no file writes in the library. The only
file read is the holidays file explicitly passed with `--holidays`.
