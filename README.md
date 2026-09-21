# Calendar Hotkey 2.0

Copy scheduling text on Windows, press **Ctrl+Alt+G**, review the result, and create Google Calendar events. Parsing is local, deterministic, bilingual (Japanese/English), and requires no paid API.

## Highlights

* Explicit and relative dates, weekdays, 12/24-hour clocks, ranges, and durations
* `Asia/Tokyo`, `Asia/Bangkok`, UTC, JST, GMT, and numeric UTC offsets
* Independent candidates from multiline or sentence-separated input
* Source text/spans, visible assumptions, missing fields, warnings, and validation status
* Safe REVIEW and AUTO policies, duplicate checking, retries, and isolated batch results
* Input/event limits and deterministic reference times for reliable testing

Examples:

```text
明日の14時から1時間、大学の面談
来週の水曜日15時からオンラインミーティング
Submit the Kaggle competition entry by October 22, 2026 at 11:59 PM UTC.
September 24, 3 PM: University meeting.
September 25, 10 AM: Research discussion.
```

## Install

Python 3.11 or later is recommended.

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
```

For Google Calendar access, put a Desktop OAuth client's `credentials.json` beside `add_calendar.py`. It is loaded only when a confirmed event is about to be created. Never commit credentials or `token.json`.

Install AutoHotkey v2 and run `calendar_hotkey.ahk`. The script preserves **Ctrl+Alt+G**, uses UTF-8 temporary files, prefers the local virtual environment, and prevents concurrent invocations.

## Modes

`REVIEW` is the default and opens an explicit confirmation dialog. Set `CALENDAR_HOTKEY_MODE=AUTO` to skip confirmation **only** for fully validated candidates. AUTO does not create an event when a required field is missing, a weekday is ambiguous, or an end time was inferred. Timezone assumptions are always shown. Canceling review performs no authentication or API call.

## Documentation

* [Architecture](docs/ARCHITECTURE.md)
* [Parser design and limitations](docs/PARSER_DESIGN.md)
* [Testing report](docs/TESTING_REPORT.md)
* [Windows validation checklist](docs/WINDOWS_VALIDATION.md)
* [Development notes](docs/DEVELOPMENT.md)

Windows desktop behavior is not claimed as verified by the Linux test suite; follow the manual checklist before relying on AUTO mode.
