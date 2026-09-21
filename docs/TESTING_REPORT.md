# Testing report

Baseline commit: `4caaf74f05cc3a16c30e17bf129c021096eceb0e`.

## Automated validation

Run:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m compileall -q add_calendar.py calendar_hotkey tests
```

The deterministic suite covers Japanese and English explicit/relative dates, weekdays, time ranges, durations, leap dates, year boundaries, cross-midnight events, named/default/numeric timezones, source spans, multiple candidates, missing and invalid values, long-input limits, Unicode, AUTO safety, duplicates, API timeouts, and partial batch failures. Google behavior uses in-memory doubles and makes no live calls.

On the Linux development environment, 26 tests pass. Windows and AutoHotkey behavior remains a manual validation item; this document does not claim otherwise.

## Synthetic performance check

The parser uses bounded regular expressions and caps both input size and output count. To measure locally without network activity:

```powershell
python -m timeit -s "from datetime import datetime; from zoneinfo import ZoneInfo; from calendar_hotkey import ScheduleParser; p=ScheduleParser(); r=datetime(2026,9,21,tzinfo=ZoneInfo('Asia/Tokyo')); t=('Tomorrow at 3 PM meeting.\n'*1000)" "p.parse(t, reference=r)"
```

Inputs over 100,000 characters fail early, preventing unbounded clipboard processing. The event cap prevents a large email from triggering an unlimited API batch.

The synthetic run on the development container parsed 1/100/1,000 scheduling lines in approximately 0.006/0.009/0.127 seconds respectively; the latter two returned the configured maximum of 50 candidates. These figures are diagnostic, not a Windows performance guarantee.

## Test policy

Never put production credentials in the repository and never run tests against a real calendar. Manual API testing should use a dedicated test calendar and disposable OAuth client.
