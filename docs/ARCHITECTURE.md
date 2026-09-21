# Calendar Hotkey 2.0 architecture

## Components

`calendar_hotkey.parser.ScheduleParser` is a deterministic, offline parser. It accepts an explicit timezone-aware reference datetime and produces typed `EventCandidate` values; it never authenticates or performs network I/O. `calendar_hotkey.google.GoogleCalendarGateway` validates candidates, checks duplicates, and isolates each API creation so one failed item does not discard the remaining results. `add_calendar.py` is the compatibility entry point used by AutoHotkey.

The contract is:

```text
clipboard -> UTF-8 temporary file -> add_calendar.py
          -> candidates -> safety policy -> review or gateway -> UTF-8 result file
```

OAuth imports are lazy. Parsing and its test suite therefore work without credentials or Google packages. OAuth scope remains limited to calendar events. Token refresh uses a finite HTTP timeout; Calendar requests use retry support supplied by the Google client.

## Safety boundary

`VALID` candidates have a title, valid start/end values, and no critical ambiguity. `REVIEW` candidates are complete enough to display but contain an inference (for example, a default duration or a bare Japanese weekday). `INVALID` candidates lack a date or start time. `AUTO` creates only `VALID` candidates; `REVIEW` creates nothing and emits a preview. The default is `REVIEW`.

No test accesses Google Calendar. API behavior is exercised through test doubles.
