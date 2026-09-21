"""Windows entry point and backwards-compatible API for Calendar Hotkey."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_hotkey import ParserConfig, ScheduleParser
from calendar_hotkey.google import GoogleCalendarGateway

BASE_DIR = Path(__file__).resolve().parent
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def extract_events(text: str, reference: datetime | None = None) -> list[dict]:
    reference = reference or datetime.now(ZoneInfo("Asia/Tokyo"))
    candidates = ScheduleParser().parse(text, reference=reference)
    return [{"title": c.title, "date": c.start.date().isoformat() if c.start else "", "start": c.start.strftime("%H:%M") if c.start else "", "end": c.end.strftime("%H:%M") if c.end else "", "all_day": False, "location": "", "description": c.description, "source_timezone": c.timezone, "timezone_explicit": c.timezone_explicit, "missing_information": c.missing_information, "ambiguity_warnings": c.ambiguity_warnings, "validation_status": c.validation_status.value, "candidate": c} for c in candidates]


def should_auto_add(event: dict) -> bool:
    return event.get("validation_status") == "valid"


def calendar_service():
    # Lazy imports keep parsing and tests independent of Google/OAuth packages.
    from google.auth.transport.requests import Request
    from google_auth_httplib2 import AuthorizedHttp
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    import httplib2
    token, credentials = BASE_DIR / "token.json", BASE_DIR / "credentials.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials.exists(): raise FileNotFoundError(f"credentials.json がありません: {credentials}")
            creds = InstalledAppFlow.from_client_secrets_file(str(credentials), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json(), encoding="utf-8")
    http = AuthorizedHttp(creds, http=httplib2.Http(timeout=20))
    return build("calendar", "v3", http=http, cache_discovery=False)


def _confirm(events: list[dict]) -> bool:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    details = "\n".join(f"• {e['title'] or '(title missing)'}\n  {e['date']} {e['start']}–{e['end']} ({e['source_timezone']})\n  {'; '.join(e['missing_information'] + e['ambiguity_warnings'])}" for e in events)
    invalid = any(e["missing_information"] for e in events)
    if invalid:
        messagebox.showwarning("Calendar Hotkey — Review", "不足情報があるため登録できません。\n\n" + details, parent=root)
        root.destroy(); return False
    answer = messagebox.askyesno("Calendar Hotkey — Review", "次の予定を登録しますか？\n\n" + details, parent=root)
    root.destroy(); return answer


def process(text: str, *, mode: str | None = None, service=None, reference: datetime | None = None, confirmer=None) -> str:
    mode = (mode or os.getenv("CALENDAR_HOTKEY_MODE", "REVIEW")).upper()
    if mode not in {"AUTO", "REVIEW"}: raise ValueError("mode must be AUTO or REVIEW")
    events = extract_events(text, reference)
    if not events: raise RuntimeError("予定を見つけられませんでした。")
    review = [e for e in events if not should_auto_add(e)]
    if mode == "AUTO" and review:
        details = "\n".join(f"• {e['title'] or '(title missing)'} | {e['date']} {e['start']} | {', '.join(e['missing_information'] + e['ambiguity_warnings'])}" for e in events)
        return f"確認が必要です ({len(review)}/{len(events)}件)\n{details}"
    confirmed = mode == "REVIEW"
    if confirmed and not (confirmer or _confirm)(events):
        return "予定は追加されませんでした。"
    gateway = GoogleCalendarGateway(service or calendar_service())
    results = gateway.create_batch((e["candidate"] for e in events), confirmed=confirmed)
    return "\n".join(f"{r.status}: {r.candidate.title}" + (f" ({r.error})" if r.error else "") for r in results)


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--auth":
        calendar_service(); print("Google Calendar authentication completed."); return 0
    if len(sys.argv) != 3:
        print("Usage: add_calendar.py <input.txt> <result.txt>"); return 2
    input_file, result_file = map(Path, sys.argv[1:])
    try:
        text = input_file.read_text(encoding="utf-8-sig")
        if not text.strip(): raise ValueError("クリップボードが空です。")
        result_file.write_text(process(text), encoding="utf-8")
        return 0
    except Exception as exc:
        result_file.write_text(f"ERROR\n{type(exc).__name__}: {exc}", encoding="utf-8")
        return 1


if __name__ == "__main__": raise SystemExit(main())
