# Windows validation checklist

Linux CI cannot validate AutoHotkey, Windows process discovery, desktop dialogs, or tray notifications. Perform these checks on Windows before enabling AUTO mode.

1. Install Python 3.11+ and AutoHotkey v2. Create `.venv`, install `requirements.txt`, and run `python -m pytest -q`.
2. Leave `CALENDAR_HOTKEY_MODE` unset (safe REVIEW default). Start `calendar_hotkey.ahk` and copy `明日の14時から16時、大学の面談`.
3. Press **Ctrl+Alt+G**. Confirm Japanese Unicode and the preview notification are intact and no calendar event was created.
4. Repeat with multiline English input containing three events. Confirm three independent previews.
5. Test empty clipboard, a 100,001-character clipboard, malformed/locked temporary files, and a missing Python executable. Confirm an actionable error rather than a silent failure.
6. Press the hotkey repeatedly while a request is running. Confirm the invocation guard reports that processing is already active.
7. Test with a repository path containing spaces and non-ASCII characters. Confirm `.venv\Scripts\pythonw.exe` is preferred and launcher fallback works.
8. With a disposable test calendar only, set `CALENDAR_HOTKEY_MODE=AUTO`, install a test OAuth `credentials.json`, and use an explicit date, range, title, and timezone. Confirm one event. Repeat the identical input and confirm duplicate suppression.
9. Revoke/expire the disposable token and confirm refresh or reauthentication behavior. Disconnect the network and confirm an error result. Restore the network and retry.
10. Verify `UTC`, `UTC-05:00`, `Asia/Bangkok`, cross-midnight, and a DST-transition event against the Google Calendar UI.

Delete disposable credentials and test events afterward. Never use a personal production calendar for validation.
