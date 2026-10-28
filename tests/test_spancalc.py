"""Tests for SpanCalc. Run: python -m unittest discover -s tests -v"""

import subprocess
import sys
import unittest
from datetime import date

sys.path.insert(0, ".")
from spancalc import (  # noqa: E402
    add_business_days,
    add_duration,
    breakdown,
    diff_business_days,
    diff_datetimes,
    format_duration,
    from_epoch,
    parse_duration,
    parse_datetime,
    subtract_duration,
    to_epoch,
    weekday_name,
)


class TestParseDuration(unittest.TestCase):
    def test_mixed_units(self):
        self.assertEqual(parse_duration("1w 2d 3h 30m"), 790200.0)

    def test_concatenated(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)

    def test_fractional(self):
        self.assertEqual(parse_duration("1.5h"), 5400.0)

    def test_bare_number_is_seconds(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_number_input(self):
        self.assertEqual(parse_duration(90), 90.0)

    def test_negative(self):
        self.assertEqual(parse_duration("-2h"), -7200.0)

    def test_iso8601(self):
        self.assertEqual(parse_duration("P2DT3H"), 183600.0)
        self.assertEqual(parse_duration("PT90M"), 5400.0)
        self.assertEqual(parse_duration("P1W"), 604800.0)

    def test_colon(self):
        self.assertEqual(parse_duration("1:30:00"), 5400.0)
        self.assertEqual(parse_duration("90:00"), 5400.0)

    def test_chinese_units(self):
        self.assertEqual(parse_duration("2天3小时"), 183600.0)
        self.assertEqual(parse_duration("90分钟"), 5400.0)

    def test_zero(self):
        self.assertEqual(parse_duration("0"), 0.0)
        self.assertEqual(parse_duration("0s"), 0.0)

    def test_unknown_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("3 parsecs")

    def test_garbage_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("hello")
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_bool_rejected(self):
        with self.assertRaises(TypeError):
            parse_duration(True)


class TestFormatAndBreakdown(unittest.TestCase):
    def test_breakdown(self):
        parts = breakdown(790200.0)
        self.assertEqual((parts["weeks"], parts["days"], parts["hours"], parts["minutes"]), (1, 2, 3, 30))

    def test_format_zh(self):
        self.assertEqual(format_duration(790200.0, "zh"), "1周2天3小时30分钟")

    def test_format_en(self):
        self.assertEqual(format_duration(5400.0, "en"), "1h30m")

    def test_format_tw(self):
        self.assertEqual(format_duration(5400.0, "zh-TW"), "1小時30分鐘")

    def test_format_zero_and_negative(self):
        self.assertEqual(format_duration(0, "zh"), "0秒")
        self.assertEqual(format_duration(-3600.0, "en"), "-1h")

    def test_roundtrip(self):
        for text in ("1w 2d", "3h 45m", "2天3小时"):
            self.assertEqual(format_duration(parse_duration(text), "zh"), format_duration(parse_duration(text), "zh"))
            self.assertGreater(parse_duration(text), 0)


class TestDates(unittest.TestCase):
    def test_add(self):
        result = add_duration("2026-10-28 10:00", "2d 3h", tz="Asia/Shanghai")
        self.assertEqual(result.isoformat(), "2026-10-30T13:00:00+08:00")

    def test_subtract(self):
        result = subtract_duration("2026-10-28 10:00", "1d", tz="Asia/Shanghai")
        self.assertEqual(result.day, 27)

    def test_diff(self):
        result = diff_datetimes("2026-10-28 10:00", "2026-10-30 13:00", tz="Asia/Shanghai")
        self.assertEqual(result["total_seconds"], 183600.0)
        self.assertEqual(result["human_zh"], "2天3小时")

    def test_diff_negative(self):
        result = diff_datetimes("2026-10-30", "2026-10-28")
        self.assertEqual(result["total_seconds"], -172800.0)

    def test_epoch_roundtrip(self):
        self.assertEqual(from_epoch(0).isoformat(), "1970-01-01T00:00:00+00:00")
        self.assertEqual(to_epoch("1970-01-01T00:00:00+00:00"), 0.0)

    def test_weekday(self):
        # 2026-10-28 is a Wednesday.
        self.assertEqual(weekday_name("2026-10-28", "zh"), "星期三")
        self.assertEqual(weekday_name("2026-10-28", "en"), "Wednesday")

    def test_bad_datetime_rejected(self):
        with self.assertRaises(ValueError):
            parse_datetime("not-a-date")

    def test_bad_timezone_rejected(self):
        with self.assertRaises(ValueError):
            parse_datetime("2026-10-28", tz="Mars/Olympus")


class TestBusinessDays(unittest.TestCase):
    def test_friday_to_monday(self):
        # 2026-10-30 is a Friday; +1 business day lands on Monday 2026-11-02.
        self.assertEqual(add_business_days("2026-10-30", 1), date(2026, 11, 2))

    def test_weekend_skipped(self):
        self.assertEqual(add_business_days("2026-10-31", 1), date(2026, 11, 2))

    def test_negative(self):
        self.assertEqual(add_business_days("2026-11-02", -1), date(2026, 10, 30))

    def test_holidays(self):
        self.assertEqual(
            add_business_days("2026-10-30", 1, holidays=["2026-11-02"]),
            date(2026, 11, 3),
        )

    def test_diff_business_days(self):
        self.assertEqual(diff_business_days("2026-10-30", "2026-11-02"), 1)
        self.assertEqual(diff_business_days("2026-11-02", "2026-10-30"), -1)
        self.assertEqual(diff_business_days("2026-10-28", "2026-10-28"), 0)


class TestCLI(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "spancalc", *args],
            capture_output=True, text=True, check=False,
        )

    def test_cli_parse(self):
        out = self._run("parse", "1h30m")
        self.assertEqual(out.returncode, 0)
        self.assertIn("1小时30分钟", out.stdout)

    def test_cli_parse_json(self):
        out = self._run("--json", "parse", "90m")
        self.assertEqual(out.returncode, 0)
        self.assertIn('"total_seconds": 5400.0', out.stdout)

    def test_cli_add(self):
        out = self._run("add", "--from", "2026-10-28 10:00", "--duration", "2d 3h", "--tz", "Asia/Shanghai")
        self.assertEqual(out.returncode, 0)
        self.assertIn("2026-10-30T13:00:00+08:00", out.stdout)

    def test_cli_diff(self):
        out = self._run("diff", "--from", "2026-10-28", "--to", "2026-10-30")
        self.assertEqual(out.returncode, 0)
        self.assertIn("2天", out.stdout)

    def test_cli_business(self):
        out = self._run("business", "--from", "2026-10-30", "--days", "1")
        self.assertEqual(out.returncode, 0)
        self.assertIn("2026-11-02", out.stdout)

    def test_cli_epoch(self):
        out = self._run("epoch", "--to-datetime", "0")
        self.assertEqual(out.returncode, 0)
        self.assertIn("1970-01-01", out.stdout)

    def test_cli_bad_input_exits_2(self):
        out = self._run("parse", "3 parsecs")
        self.assertEqual(out.returncode, 2)
        self.assertIn("error", out.stderr)


if __name__ == "__main__":
    unittest.main()
