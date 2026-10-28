[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

# ⏱️ SpanCalc

> Stop reaching for a calendar or a calculator for "what time is it in 90 minutes" or "which day is one business day after Friday". SpanCalc answers in one command — and if the input is wrong, it errors out instead of quietly giving you a wrong date.

## 🎉 Introduction

Scripts, CI jobs, and data pipelines are full of small time arithmetic: "this batch takes 2 days and 3 hours, when does it finish?", "how long is it between these two timestamps?", "it is Friday and we promised delivery in 1 business day — which day is that?", "what time is this timestamp in local time?"

The usual answers are a hand-rolled `date` incantation, an online converter, or a date library pulled in for one tiny calculation — overkill, and not always correct. SpanCalc is built for exactly these small jobs: a **zero-dependency, pure-calculation, fully offline** Python tool that works as a CLI and as an importable library. It never times, tracks, phones home, or stores state. It only calculates.

## ✨ Features

- 🗣️ **Human-readable durations** — `1w 2d 3h 30m`, `1h30m`, `1.5h`, `2天3小时`, `PT90M` (ISO 8601), `1:30:00`, all accepted
- 📅 **Date arithmetic** — add a duration to any date, with IANA timezones such as `Asia/Shanghai`
- ↔️ **Differences** — how long between two datetimes, broken into weeks / days / hours / minutes, plus business days
- 💼 **Business days** — weekends skipped by default; holidays come from a file you supply, never from a built-in table that goes stale
- 🕰️ **Epoch conversion** — datetimes and Unix timestamps, both directions, UTC by default, any timezone on request
- 🧩 **Usable as a library** — `parse_duration`, `add_duration`, `diff_datetimes` and friends are all importable
- 🛡️ **Fails loudly** — unknown units, malformed dates, and unknown timezones error out with exit code 2, so scripts and CI can rely on it
- 🪶 **Zero dependencies** — Python 3.9+ standard library only

## 🚀 Quick Start

Requirements: Python 3.9 or newer, no dependencies to install.

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m spancalc parse "1w 2d 3h 30m"
```

```bash
# Output (default language is Chinese): 1周2天3小时30分钟
# With --lang en: 1w2d3h30m
python -m spancalc parse "1h30m"
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Shanghai
python -m spancalc diff --from "2026-10-28" --to "2026-10-30"
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc epoch --to-datetime 0
```

As a library:

```python
from spancalc import parse_duration, add_duration, diff_datetimes

parse_duration("1h30m")          # 5400.0 (seconds)
add_duration("2026-10-28 10:00", "2d 3h", tz="Asia/Shanghai")
diff_datetimes("2026-10-28", "2026-10-30")["human_en"]  # '2d'
```

## 📖 Detailed Guide

### ⏳ Parsing durations: `parse`

```bash
python -m spancalc parse "1w 2d 3h 30m"
python -m spancalc parse "2天3小时"
python -m spancalc parse "PT90M"
python -m spancalc parse "1:30:00"
python -m spancalc --json parse "90m"
```

Accepted spellings: mixed units (`1w 2d 3h 30m`), concatenated (`1h30m`), fractional (`1.5h`), Chinese units (`天 / 小时 / 分钟 / 秒 / 周 / 年 / 月`), ISO 8601 (`P2DT3H`, `PT90M`), colon form (`1:30:00` is 1 hour 30 minutes, `90:00` is 90 minutes), a bare number (seconds), and a leading minus (`-2h`). Units: `w = 7 days, d = 24 hours`; `year` and `month` are fixed conversions (1 year = 365 days, 1 month = 30 days), stated openly in the docs — they are not calendar months.

### 🔄 Converting units: `convert`

```bash
python -m spancalc convert "90m" --to hours
python -m spancalc convert "2d" --to seconds
```

`--to` accepts `weeks / days / hours / minutes / seconds / milliseconds`.

### ➕➖ Adding and subtracting: `add` / `sub`

```bash
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Shanghai
python -m spancalc sub --from "2026-10-28 10:00" --duration "1d"
```

Dates accept `YYYY-MM-DD`, `YYYY-MM-DD HH:MM[:SS]`, and ISO 8601. Input without timezone information is read as UTC; pass `--tz` to read it in that timezone; if the input already carries an offset, do not pass `--tz`.

### ↔️ Differences: `diff`

```bash
python -m spancalc diff --from "2026-10-28 10:00" --to "2026-10-30 13:00" --tz Asia/Shanghai
python -m spancalc --json diff --from "2026-10-28" --to "2026-10-30"
```

Output includes total seconds, a weeks / days / hours / minutes breakdown, human-readable strings in Chinese and English, and the number of business days between the two dates (`business_days`).

### 💼 Business days: `business`

```bash
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc business --from "2026-10-30" --days 1 --holidays examples/holidays.example.txt
```

Weekends are skipped by default; a negative `--days` walks backwards. The holidays file holds one `YYYY-MM-DD` date per line, with `#` lines as comments. The rule is explicit: the start date itself is never counted; the day you land on after counting N business days is the answer.

### 🕰️ Epochs: `epoch`

```bash
python -m spancalc epoch --from-datetime "2026-10-28 10:00" --tz Asia/Shanghai
python -m spancalc epoch --to-datetime 1761612000
python -m spancalc epoch --to-datetime 0 --tz Asia/Shanghai
```

Pass exactly one of `--from-datetime` / `--to-datetime`; passing both or neither is an error.

### 🧩 Output format and exit codes

Every subcommand accepts the global `--json` flag for machine-readable output, so scripts and CI can parse it:

```bash
python -m spancalc --json parse "90m"
```

```json
{
  "duration": "90m",
  "total_seconds": 5400.0,
  "breakdown": {
    "weeks": 0,
    "days": 0,
    "hours": 1,
    "minutes": 30,
    "seconds": 0,
    "sign": 1,
    "total_seconds": 5400.0
  },
  "human": "1小时30分钟"
}
```

Exit codes: `0` for success, `2` for bad input (unknown unit, parse failure, unknown timezone, and so on).

## 🧠 Design and Roadmap

SpanCalc aims to be the smallest useful time-calculation tool: deterministic calculation only, no timing, tracking, or scheduling. The core (`spancalc/core.py`) does no I/O and holds no global state, so it is easy to test and easy to import; the CLI (`spancalc/cli.py`) owns argument parsing, printing, and exit codes.

How it differs: many date libraries try to do everything, so a small calculation drags in dependencies; many online converters need the network and cannot run in a script. SpanCalc is the opposite: **zero dependencies, offline, loud errors, pipe-friendly output**. And it does not do time tracking — that is a different tool's job. SpanCalc calculates; it does not record.

Roadmap:

- v1.1: relative expressions ("next Monday", "end of month") — only if their meaning stays unambiguous, otherwise not at all
- v1.2: batch mode, reading many durations or dates from standard input in one run
- v1.3: per-region holiday data files (still explicitly passed by the user, still offline)

## 📦 Packaging and Deployment

This project is a **library / CLI tool**, so by its release policy it ships no Release: clone it and run it directly, no packaging step needed.

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m unittest discover -s tests -v
python -m spancalc --help
```

Optional system-wide install:

```bash
pip install .
spancalc parse "1h30m"
```

Compatibility: Python 3.9+ on Windows, macOS, and Linux. Timezone support uses the system's IANA database through Python's `zoneinfo`; on unusually minimal systems you may need to install `tzdata`.

FAQ:

- **Q: What do I do about `Unknown timezone`?** A: Check the spelling (for example `Asia/Shanghai`) and make sure the system has a timezone database.
- **Q: Why is `1 month` not a calendar month?** A: A duration string's "month" has no fixed length, so this tool converts it as 30 days and says so in the docs and code comments. For exact calendar-month arithmetic, use a date library.
- **Q: Why no built-in holidays?** A: Holidays change every year and differ by region, so a built-in table would go stale. Pass your own file with `--holidays` and it stays correct.

## 🤝 Contributing

Issues and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). The basics: keep changes small, add tests, update all three README versions together, and cover new behaviour with test cases.

## 📄 License

MIT. See [LICENSE](LICENSE).
