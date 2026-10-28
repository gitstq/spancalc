# Contributing to SpanCalc

Thank you for considering a contribution. SpanCalc is deliberately small:
zero dependencies, pure calculation, no network, no storage, no timers.

## How to contribute

1. Fork the repository and create a focused branch.
2. Keep changes small and covered by tests: add a case to
   `tests/test_spancalc.py` for every new behaviour and every bug fix.
3. Run the full suite before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

4. Follow the existing style: functions raise `ValueError` on bad input
   instead of guessing, public functions are documented with their
   contract, and CLI exit code `2` means bad input.
5. Update all three README versions (`README.md`, `README.zh-TW.md`,
   `README.en.md`) when you change user-facing behaviour.

## What fits here

- New duration spellings that are unambiguous (with tests and docs).
- New calendar helpers that stay deterministic and offline.
- Better error messages and output formats.

## What does not fit here

- Time tracking, timers, or Pomodoro features (a different tool's job).
- Network calls, API clients, or stored state.
- Calendar-accurate month arithmetic disguised as a fixed unit: month
  and year are documented approximations (30 / 365 days) in this tool.

## Reporting issues

Please include the exact command, the input, the output you got, and
the output you expected. A minimal failing test case is very welcome.
