from __future__ import annotations

import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events"
]

JST = timezone(timedelta(hours=9))
TZ_NAME = "Asia/Tokyo"


# ============================================================
# Language data
# ============================================================

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

JP_WEEKDAYS = {
    "月": 0,
    "火": 1,
    "水": 2,
    "木": 3,
    "金": 4,
    "土": 5,
    "日": 6,
}

EN_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,

    "mon": 0,
    "tue": 1,
    "tues": 1,
    "wed": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

# 固定UTC offset
# PST/PDTのように標準時・夏時間が明示された表記のみ扱う
TZ_OFFSETS = {
    "UTC": 0,
    "GMT": 0,

    "JST": 9,
    "KST": 9,

    # Anywhere on Earth
    "AOE": -12,

    "PST": -8,
    "PDT": -7,

    "MST": -7,
    "MDT": -6,

    "CST": -6,
    "CDT": -5,

    "EST": -5,
    "EDT": -4,

    "CET": 1,
    "CEST": 2,

    "BST": 1,
}

DEADLINE_KEYWORDS = [
    "deadline",
    "submission deadline",
    "final submission",
    "final submission deadline",
    "due",
    "due date",
    "closes",
    "closing",
    "registration closes",
    "締切",
    "期限",
    "提出期限",
    "応募期限",
]

VAGUE_WORDS = [
    "morning",
    "afternoon",
    "evening",
    "tonight",
    "sometime",
    "around",
    "approximately",
    "approx",
    "about",
    "tba",
    "tbd",
    "午前中",
    "夕方",
    "夜",
    "頃",
    "ごろ",
    "くらい",
    "ぐらい",
    "あたり",
    "未定",
]


# ============================================================
# Google Calendar authentication
# ============================================================

def calendar_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):
            creds.refresh(Request())

        else:

            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json がありません: {CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0
            )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return build(
        "calendar",
        "v3",
        credentials=creds,
    )


# ============================================================
# Text normalization
# ============================================================

def normalize_text(text: str) -> str:
    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    text = re.sub(
        r"\ba\.?\s*m\.?",
        "AM",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bp\.?\s*m\.?",
        "PM",
        text,
        flags=re.IGNORECASE,
    )

    for month in [
        "Jan", "Feb", "Mar", "Apr",
        "Jun", "Jul", "Aug",
        "Sep", "Sept", "Oct",
        "Nov", "Dec",
    ]:
        text = re.sub(
            rf"\b{month}\.",
            month,
            text,
            flags=re.IGNORECASE,
        )

    return text


def segments(text: str) -> list[str]:
    text = normalize_text(text)

    parts = re.split(
        r"(?<=[。！？!?])\s*|\n+",
        text,
    )

    return [
        item.strip()
        for item in parts
        if item.strip()
    ]


# ============================================================
# Date parsing
# ============================================================

def safe_date(
    year: int,
    month: int,
    day: int,
):
    try:
        return date(
            year,
            month,
            day,
        )
    except ValueError:
        return None


def infer_year(
    month: int,
    day: int,
    today: date,
):
    result = safe_date(
        today.year,
        month,
        day,
    )

    if result is None:
        return None

    # 年が省略され、日付がすでに過ぎている場合は翌年
    if result < today - timedelta(days=1):
        result = safe_date(
            today.year + 1,
            month,
            day,
        )

    return result


def parse_date(
    text: str,
    today: date,
):

    # 2026-10-19 / 2026/10/19 / 2026年10月19日
    match = re.search(
        r"(?<!\d)"
        r"(20\d{2})"
        r"[-/.年]\s*"
        r"(\d{1,2})"
        r"[-/.月]\s*"
        r"(\d{1,2})"
        r"(?:日)?"
        r"(?!\d)",
        text,
    )

    if match:
        return safe_date(
            int(match[1]),
            int(match[2]),
            int(match[3]),
        )

    # 10月19日
    match = re.search(
        r"(?<!\d)"
        r"(\d{1,2})\s*月\s*"
        r"(\d{1,2})\s*日",
        text,
    )

    if match:
        return infer_year(
            int(match[1]),
            int(match[2]),
            today,
        )

    month_pattern = "|".join(
        sorted(
            MONTHS.keys(),
            key=len,
            reverse=True,
        )
    )

    # October 19, 2026
    # Oct 19 2026
    match = re.search(
        rf"\b({month_pattern})"
        rf"\s+"
        rf"(\d{{1,2}})"
        rf"(?:st|nd|rd|th)?"
        rf"(?:,\s*|\s+)?"
        rf"(20\d{{2}})?"
        rf"\b",
        text,
        re.IGNORECASE,
    )

    if match:
        month = MONTHS[
            match[1].lower()
        ]

        day = int(
            match[2]
        )

        if match[3]:
            return safe_date(
                int(match[3]),
                month,
                day,
            )

        return infer_year(
            month,
            day,
            today,
        )

    # 19 October 2026
    # 19 Oct 2026
    match = re.search(
        rf"\b"
        rf"(\d{{1,2}})"
        rf"(?:st|nd|rd|th)?"
        rf"\s+"
        rf"({month_pattern})"
        rf"(?:,\s*|\s+)?"
        rf"(20\d{{2}})?"
        rf"\b",
        text,
        re.IGNORECASE,
    )

    if match:
        day = int(
            match[1]
        )

        month = MONTHS[
            match[2].lower()
        ]

        if match[3]:
            return safe_date(
                int(match[3]),
                month,
                day,
            )

        return infer_year(
            month,
            day,
            today,
        )

    # 10/19 / 10/19/2026
    match = re.search(
        r"(?<!\d)"
        r"(\d{1,2})/"
        r"(\d{1,2})"
        r"(?:/(20\d{2}))?"
        r"(?!\d)",
        text,
    )

    if match:
        first = int(
            match[1]
        )

        second = int(
            match[2]
        )

        year = (
            int(match[3])
            if match[3]
            else None
        )

        # 通常は month/day。
        # 先頭 > 12 なら day/month とみなす
        if first > 12:
            day = first
            month = second
        else:
            month = first
            day = second

        if year:
            return safe_date(
                year,
                month,
                day,
            )

        return infer_year(
            month,
            day,
            today,
        )

    # 日本語相対日付
    if "明後日" in text:
        return today + timedelta(days=2)

    if "明日" in text:
        return today + timedelta(days=1)

    if (
        "今日" in text
        or "本日" in text
    ):
        return today

    match = re.search(
        r"(今週|来週|再来週)"
        r"(?:の)?\s*"
        r"([月火水木金土日])"
        r"(?:曜(?:日)?)?",
        text,
    )

    if match:
        monday = (
            today
            - timedelta(
                days=today.weekday()
            )
        )

        week = {
            "今週": 0,
            "来週": 1,
            "再来週": 2,
        }[match[1]]

        return monday + timedelta(
            days=(
                week * 7
                + JP_WEEKDAYS[match[2]]
            )
        )

    # 水曜日 / 次の水曜日
    match = re.search(
        r"(?:次の)?\s*"
        r"([月火水木金土日])"
        r"曜(?:日)?",
        text,
    )

    if match:
        target = JP_WEEKDAYS[
            match[1]
        ]

        delta = (
            target
            - today.weekday()
        ) % 7

        if delta == 0:
            delta = 7

        return today + timedelta(
            days=delta
        )

    lower = text.lower()

    # English relative dates
    if "day after tomorrow" in lower:
        return today + timedelta(days=2)

    if re.search(
        r"\btomorrow\b",
        lower,
    ):
        return today + timedelta(days=1)

    if re.search(
        r"\btoday\b",
        lower,
    ):
        return today

    weekday_pattern = "|".join(
        sorted(
            EN_WEEKDAYS.keys(),
            key=len,
            reverse=True,
        )
    )

    # next Friday
    match = re.search(
        rf"\bnext\s+"
        rf"({weekday_pattern})\b",
        lower,
    )

    if match:
        target = EN_WEEKDAYS[
            match[1]
        ]

        delta = (
            target
            - today.weekday()
        ) % 7

        if delta == 0:
            delta = 7

        return today + timedelta(
            days=delta
        )

    # this Friday
    match = re.search(
        rf"\bthis\s+"
        rf"({weekday_pattern})\b",
        lower,
    )

    if match:
        target = EN_WEEKDAYS[
            match[1]
        ]

        delta = (
            target
            - today.weekday()
        ) % 7

        return today + timedelta(
            days=delta
        )

    return None


# ============================================================
# Time parsing
# ============================================================

def parse_english_clock(
    token: str,
):
    token = (
        token
        .strip()
        .lower()
        .replace(" ", "")
    )

    if token == "noon":
        return time(
            12,
            0,
        )

    if token == "midnight":
        return time(
            0,
            0,
        )

    match = re.fullmatch(
        r"(\d{1,2})"
        r"(?::(\d{2}))?"
        r"(am|pm)?",
        token,
    )

    if not match:
        return None

    hour = int(
        match[1]
    )

    minute = int(
        match[2] or 0
    )

    am_pm = match[3]

    if am_pm:

        if not 1 <= hour <= 12:
            return None

        if (
            am_pm == "pm"
            and hour < 12
        ):
            hour += 12

        if (
            am_pm == "am"
            and hour == 12
        ):
            hour = 0

    if (
        hour > 23
        or minute > 59
    ):
        return None

    return time(
        hour,
        minute,
    )


def parse_japanese_clock(
    token: str,
):
    match = re.fullmatch(
        r"(?:(午前|午後)\s*)?"
        r"(\d{1,2})\s*時"
        r"(?:\s*(\d{1,2})\s*分)?",
        token.strip(),
    )

    if not match:
        return None

    am_pm = match[1]

    hour = int(
        match[2]
    )

    minute = int(
        match[3] or 0
    )

    if (
        am_pm == "午後"
        and hour < 12
    ):
        hour += 12

    if (
        am_pm == "午前"
        and hour == 12
    ):
        hour = 0

    if (
        hour > 23
        or minute > 59
    ):
        return None

    return time(
        hour,
        minute,
    )


def parse_times(
    text: str,
):
    jp_token = (
        r"(?:(?:午前|午後)\s*)?"
        r"\d{1,2}\s*時"
        r"(?:\s*\d{1,2}\s*分)?"
    )

    # 14時から15時
    match = re.search(
        rf"({jp_token})"
        rf"\s*"
        rf"(?:から|〜|～|~|-|－|–|—)"
        rf"\s*"
        rf"({jp_token})",
        text,
    )

    if match:
        start = parse_japanese_clock(
            match[1]
        )

        end = parse_japanese_clock(
            match[2]
        )

        if start and end:
            # 午後2時から3時 のようなケース
            if (
                end <= start
                and start.hour >= 12
                and end.hour < 12
                and "午前" not in match[2]
                and "午後" not in match[2]
            ):
                candidate_hour = (
                    end.hour + 12
                )

                if candidate_hour <= 23:
                    end = time(
                        candidate_hour,
                        end.minute,
                    )

            return start, end

    en_token = (
        r"(?:"
        r"\d{1,2}:\d{2}"
        r"\s*(?:AM|PM|am|pm)?"
        r"|"
        r"\d{1,2}\s*(?:AM|PM|am|pm)"
        r"|noon"
        r"|midnight"
        r")"
    )

    # 2 PM - 3 PM
    # 14:00 - 15:00
    match = re.search(
        rf"({en_token})"
        rf"\s*"
        rf"(?:-|–|—|to|until|through)"
        rf"\s*"
        rf"({en_token})",
        text,
        re.IGNORECASE,
    )

    if match:
        start = parse_english_clock(
            match[1]
        )

        end = parse_english_clock(
            match[2]
        )

        if start and end:

            # 2 PM - 3 のような形は現在対象外。
            # 2 PM - 3 PM は正常処理
            return start, end

    # 日本語の単一時刻
    match = re.search(
        rf"({jp_token})",
        text,
    )

    if match:
        start = parse_japanese_clock(
            match[1]
        )

        if start:
            return start, None

    # English single time
    match = re.search(
        rf"(?:\bat\s*)?"
        rf"({en_token})",
        text,
        re.IGNORECASE,
    )

    if match:
        start = parse_english_clock(
            match[1]
        )

        if start:
            return start, None

    return None, None


# ============================================================
# Time zone parsing
# ============================================================

def detect_timezone(
    text: str,
):
    """
    returns:
        label: str
        offset_hours: float
        explicit: bool
    """

    # Anywhere on Earth
    if re.search(
        r"Anywhere\s+on\s+Earth",
        text,
        re.IGNORECASE,
    ):
        return "AoE", -12, True

    match = re.search(
        r"\b("
        r"UTC|GMT|JST|KST|AoE|"
        r"PST|PDT|MST|MDT|"
        r"CST|CDT|EST|EDT|"
        r"CET|CEST|BST"
        r")\b",
        text,
        re.IGNORECASE,
    )

    if match:
        label = (
            match[1]
            .upper()
        )

        if label == "AOE":
            return "AoE", -12, True

        return (
            label,
            TZ_OFFSETS[label],
            True,
        )

    # UTC+2 / UTC-05 / UTC+09:00
    match = re.search(
        r"\b(?:UTC|GMT)"
        r"\s*([+-])"
        r"\s*(\d{1,2})"
        r"(?::?(\d{2}))?"
        r"\b",
        text,
        re.IGNORECASE,
    )

    if match:
        sign = (
            1
            if match[1] == "+"
            else -1
        )

        hour = int(
            match[2]
        )

        minute = int(
            match[3] or 0
        )

        offset = sign * (
            hour + minute / 60
        )

        label = (
            f"UTC{match[1]}"
            f"{hour:02d}:"
            f"{minute:02d}"
        )

        return label, offset, True

    # タイムゾーン未指定
    # 日本ユーザー向けに表示・通常予定はJST扱い
    return "JST (default)", 9, False


def convert_to_jst(
    event_date: date,
    start: time,
    end: time | None,
    offset_hours: float,
):
    source_timezone = timezone(
        timedelta(
            hours=offset_hours
        )
    )

    start_dt = datetime.combine(
        event_date,
        start,
        tzinfo=source_timezone,
    )

    if end is None:
        end_dt = None

    else:
        end_dt = datetime.combine(
            event_date,
            end,
            tzinfo=source_timezone,
        )

        if end_dt <= start_dt:
            end_dt += timedelta(
                days=1
            )

    jst_start = (
        start_dt
        .astimezone(JST)
    )

    jst_end = (
        end_dt
        .astimezone(JST)
        if end_dt
        else None
    )

    return (
        jst_start,
        jst_end,
    )


# ============================================================
# Classification
# ============================================================

def is_deadline_text(
    text: str,
):
    lower = text.lower()

    return any(
        keyword.lower() in lower
        for keyword in DEADLINE_KEYWORDS
    )


def has_vague_expression(
    text: str,
):
    lower = text.lower()

    return any(
        word.lower() in lower
        for word in VAGUE_WORDS
    )


def should_auto_add(
    event: dict,
) -> bool:
    """
    明確な予定:
        確認画面なしで自動追加

    曖昧な予定:
        確認画面を表示
    """

    # 日付のみ → 確認
    if event.get(
        "all_day"
    ):
        return False

    if not event.get(
        "date"
    ):
        return False

    if not event.get(
        "start"
    ):
        return False

    if not event.get(
        "end"
    ):
        return False

    title = (
        event
        .get(
            "title",
            "",
        )
        .strip()
    )

    if (
        not title
        or title == "予定"
    ):
        return False

    # evening / 頃 / 未定など
    if event.get(
        "vague"
    ):
        return False

    # 終了時間を自動推測した通常予定
    # → 必ず確認
    #
    # deadline は単一時刻が普通なので
    # 15分イベントとして自動追加可
    if (
        event.get(
            "end_inferred"
        )
        and not event.get(
            "deadline"
        )
    ):
        return False

    # 海外コンペ締切なのに
    # UTC/JST/AoE等が書かれていない
    # → 必ず確認
    if (
        event.get(
            "deadline"
        )
        and not event.get(
            "timezone_explicit"
        )
    ):
        return False

    return True


# ============================================================
# Event extraction
# ============================================================

def contains_date(
    text: str,
):
    today = (
        datetime
        .now(JST)
        .date()
    )

    return (
        parse_date(
            text,
            today,
        )
        is not None
    )


def extract_location(
    text: str,
):
    patterns = [
        (
            r"(?:場所|会場|集合場所)"
            r"\s*(?:は|:|：)\s*"
            r"([^。\n、]+)"
        ),
        (
            r"(?:location|venue)"
            r"\s*(?::|-)\s*"
            r"([^\n,.]+)"
        ),
        (
            r"\b("
            r"Zoom|"
            r"Google Meet|"
            r"Microsoft Teams"
            r")\b"
        ),
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = (
                match[1]
                .strip()
            )

            value = re.sub(
                r"\s*(?:です|になります|予定です)$",
                "",
                value,
            )

            return value[:120]

    return ""


def clean_title(
    text: str,
):
    text = (
        text
        .replace("\n", " ")
        .strip()
    )

    # URLs除去
    text = re.sub(
        r"https?://\S+",
        "",
        text,
    )

    # YYYY-MM-DD等
    text = re.sub(
        r"20\d{2}[-/.年]\s*"
        r"\d{1,2}[-/.月]\s*"
        r"\d{1,2}(?:日)?",
        " ",
        text,
    )

    # 10月19日
    text = re.sub(
        r"\d{1,2}\s*月\s*"
        r"\d{1,2}\s*日",
        " ",
        text,
    )

    month_names = "|".join(
        sorted(
            MONTHS.keys(),
            key=len,
            reverse=True,
        )
    )

    # October 19 2026
    text = re.sub(
        rf"\b(?:{month_names})\s+"
        rf"\d{{1,2}}"
        rf"(?:st|nd|rd|th)?"
        rf"(?:,\s*|\s+)?"
        rf"(?:20\d{{2}})?",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # 19 October 2026
    text = re.sub(
        rf"\b\d{{1,2}}"
        rf"(?:st|nd|rd|th)?\s+"
        rf"(?:{month_names})"
        rf"(?:,\s*|\s+)?"
        rf"(?:20\d{{2}})?",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # 時刻
    text = re.sub(
        r"\b\d{1,2}:\d{2}"
        r"\s*(?:AM|PM)?\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\b\d{1,2}\s*(?:AM|PM)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\d{1,2}\s*時"
        r"(?:\s*\d{1,2}\s*分)?",
        " ",
        text,
    )

    # TZ
    text = re.sub(
        r"\b(?:"
        r"UTC|GMT|JST|KST|AoE|"
        r"PST|PDT|MST|MDT|"
        r"CST|CDT|EST|EDT|"
        r"CET|CEST|BST"
        r")\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # 不要な接続語
    text = re.sub(
        r"\b(?:at|on)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"(?:から|〜|～|まで)",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = text.strip(
        " -–—:：,、。"
    )

    if not text:
        return "予定"

    return text[:80]


def make_title(
    part: str,
    previous: str | None,
    deadline: bool,
):
    current = clean_title(
        part
    )

    generic_deadlines = {
        "deadline",
        "submission deadline",
        "final submission deadline",
        "final submission",
        "due",
        "due date",
        "締切",
        "提出締切",
        "提出期限",
    }

    normalized = (
        current
        .strip()
        .lower()
        .strip(":：- ")
    )

    if (
        deadline
        and previous
        and (
            normalized in generic_deadlines
            or len(current) <= 22
        )
    ):
        previous_title = clean_title(
            previous
        )

        if (
            previous_title
            and previous_title != "予定"
        ):
            return (
                previous_title
                + " - "
                + (
                    "Deadline"
                    if not any(
                        x in current.lower()
                        for x in [
                            "deadline",
                            "締切",
                            "期限",
                        ]
                    )
                    else current
                )
            )[:80]

    return current[:80]


def extract_events(
    text: str,
):
    original = normalize_text(
        text
    )

    parts = segments(
        original
    )

    today = (
        datetime
        .now(JST)
        .date()
    )

    events = []

    for index, part in enumerate(
        parts
    ):
        event_date = parse_date(
            part,
            today,
        )

        if event_date is None:
            continue

        previous = (
            parts[index - 1]
            if index > 0
            else None
        )

        context_parts = []

        if (
            previous
            and not contains_date(
                previous
            )
        ):
            context_parts.append(
                previous
            )

        context_parts.append(
            part
        )

        # 続く2文まで場所/TZなどとして参照
        for position in range(
            index + 1,
            min(
                len(parts),
                index + 3,
            ),
        ):
            next_part = parts[
                position
            ]

            if contains_date(
                next_part
            ):
                break

            context_parts.append(
                next_part
            )

        context = " ".join(
            context_parts
        )

        start, end = parse_times(
            part
        )

        if start is None:
            start, end = parse_times(
                context
            )

        (
            source_timezone,
            source_offset,
            timezone_explicit,
        ) = detect_timezone(
            context
        )

        deadline = is_deadline_text(
            context
        )

        vague = has_vague_expression(
            context
        )

        end_inferred = False

        if start is None:
            # 時刻なし
            event_day = event_date

            start_string = ""
            end_string = ""

            all_day = True

        else:

            # 終了時刻なし
            if end is None:
                end_inferred = True

                # deadlineは15分枠、
                # その他は仮で1時間
                duration = (
                    15
                    if deadline
                    else 60
                )

                temp = (
                    datetime.combine(
                        event_date,
                        start,
                    )
                    + timedelta(
                        minutes=duration
                    )
                )

                end = temp.time()

            (
                jst_start,
                jst_end,
            ) = convert_to_jst(
                event_date,
                start,
                end,
                source_offset,
            )

            event_day = (
                jst_start.date()
            )

            start_string = (
                jst_start.strftime(
                    "%H:%M"
                )
            )

            end_string = (
                jst_end.strftime(
                    "%H:%M"
                )
            )

            all_day = False

        title = make_title(
            part,
            previous,
            deadline,
        )

        description = original

        if (
            timezone_explicit
            and source_timezone
            not in {
                "JST",
            }
            and not all_day
        ):
            description = (
                f"[Converted from "
                f"{source_timezone} to JST]\n\n"
                + description
            )

        events.append({
            "title": title,
            "date": event_day.isoformat(),
            "start": start_string,
            "end": end_string,
            "all_day": all_day,
            "location": extract_location(
                context
            ),
            "description": description,

            # 表示用
            "source_timezone": (
                source_timezone
            ),

            # 自動判定用
            "deadline": deadline,
            "timezone_explicit": (
                timezone_explicit
            ),
            "end_inferred": (
                end_inferred
            ),
            "vague": vague,
        })

    # 同一候補除去
    unique = []
    seen = set()

    for event in events:
        key = (
            event["date"],
            event["start"],
            event["end"],
            event["title"].casefold(),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            event
        )

    return unique


# ============================================================
# Review window
# ============================================================

def review_event(
    event,
    index,
    total,
):
    result = {
        "action": "cancel",
        "event": None,
    }

    root = tk.Tk()

    root.title(
        f"Google Calendar - "
        f"予定確認 ({index}/{total})"
    )

    root.geometry(
        "650x570"
    )

    root.resizable(
        True,
        True,
    )

    root.attributes(
        "-topmost",
        True,
    )

    frame = tk.Frame(
        root,
        padx=16,
        pady=16,
    )

    frame.pack(
        fill="both",
        expand=True,
    )

    frame.columnconfigure(
        1,
        weight=1,
    )

    frame.rowconfigure(
        8,
        weight=1,
    )

    title_var = tk.StringVar(
        value=event["title"]
    )

    date_var = tk.StringVar(
        value=event["date"]
    )

    start_var = tk.StringVar(
        value=event["start"]
    )

    end_var = tk.StringVar(
        value=event["end"]
    )

    location_var = tk.StringVar(
        value=event["location"]
    )

    all_day_var = tk.BooleanVar(
        value=event["all_day"]
    )

    source_tz = event.get(
        "source_timezone",
        "JST (default)",
    )

    tk.Label(
        frame,
        text=(
            f"予定 {index}/{total}    "
            f"入力側TZ: {source_tz}    "
            f"登録TZ: JST"
        ),
        font=(
            "Yu Gothic UI",
            10,
            "bold",
        ),
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(0, 10),
    )

    fields = [
        (
            "タイトル / Title",
            title_var,
        ),
        (
            "日付 / Date",
            date_var,
        ),
        (
            "開始 / Start",
            start_var,
        ),
        (
            "終了 / End",
            end_var,
        ),
        (
            "場所 / Location",
            location_var,
        ),
    ]

    entries = []

    for row, (
        label,
        variable,
    ) in enumerate(
        fields,
        start=1,
    ):
        tk.Label(
            frame,
            text=label,
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=5,
            padx=(0, 10),
        )

        entry = tk.Entry(
            frame,
            textvariable=variable,
        )

        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=5,
        )

        entries.append(
            entry
        )

    tk.Checkbutton(
        frame,
        text="終日 / All day",
        variable=all_day_var,
    ).grid(
        row=6,
        column=1,
        sticky="w",
    )

    tk.Label(
        frame,
        text="説明 / Source",
    ).grid(
        row=8,
        column=0,
        sticky="nw",
        pady=5,
    )

    description = tk.Text(
        frame,
        height=12,
        wrap="word",
    )

    description.grid(
        row=8,
        column=1,
        sticky="nsew",
        pady=5,
    )

    description.insert(
        "1.0",
        event["description"],
    )

    def toggle_time_fields(*_):
        state = (
            "disabled"
            if all_day_var.get()
            else "normal"
        )

        entries[2].configure(
            state=state
        )

        entries[3].configure(
            state=state
        )

    all_day_var.trace_add(
        "write",
        toggle_time_fields,
    )

    toggle_time_fields()

    def add():
        try:
            datetime.strptime(
                date_var
                .get()
                .strip(),
                "%Y-%m-%d",
            )

            if not all_day_var.get():
                datetime.strptime(
                    start_var
                    .get()
                    .strip(),
                    "%H:%M",
                )

                datetime.strptime(
                    end_var
                    .get()
                    .strip(),
                    "%H:%M",
                )

        except ValueError:
            messagebox.showerror(
                "入力エラー",
                "Date は YYYY-MM-DD、"
                "Time は HH:MM で入力してください。",
                parent=root,
            )

            return

        if not title_var.get().strip():
            messagebox.showerror(
                "入力エラー",
                "タイトルを入力してください。",
                parent=root,
            )

            return

        result["action"] = "add"

        result["event"] = {
            "title": (
                title_var
                .get()
                .strip()
            ),
            "date": (
                date_var
                .get()
                .strip()
            ),
            "start": (
                start_var
                .get()
                .strip()
            ),
            "end": (
                end_var
                .get()
                .strip()
            ),
            "all_day": (
                all_day_var.get()
            ),
            "location": (
                location_var
                .get()
                .strip()
            ),
            "description": (
                description
                .get(
                    "1.0",
                    "end",
                )
                .strip()
            ),
        }

        root.destroy()

    def skip():
        result["action"] = "skip"
        root.destroy()

    buttons = tk.Frame(
        frame
    )

    buttons.grid(
        row=9,
        column=0,
        columnspan=2,
        sticky="e",
        pady=(12, 0),
    )

    tk.Button(
        buttons,
        text="追加 / Add",
        width=13,
        command=add,
    ).pack(
        side="left",
        padx=4,
    )

    tk.Button(
        buttons,
        text="スキップ / Skip",
        width=13,
        command=skip,
    ).pack(
        side="left",
        padx=4,
    )

    tk.Button(
        buttons,
        text="キャンセル",
        width=13,
        command=root.destroy,
    ).pack(
        side="left",
        padx=4,
    )

    root.mainloop()

    return result


# ============================================================
# Calendar helpers
# ============================================================

def jst_datetime(
    day: str,
    clock: str,
):
    parsed_date = (
        datetime.strptime(
            day,
            "%Y-%m-%d",
        )
        .date()
    )

    parsed_time = (
        datetime.strptime(
            clock,
            "%H:%M",
        )
        .time()
    )

    return datetime.combine(
        parsed_date,
        parsed_time,
        tzinfo=JST,
    )


def is_duplicate(
    service,
    event,
):
    parsed_day = (
        datetime.strptime(
            event["date"],
            "%Y-%m-%d",
        )
        .date()
    )

    if event["all_day"]:
        start = datetime.combine(
            parsed_day,
            time.min,
            tzinfo=JST,
        )

        end = (
            start
            + timedelta(days=1)
        )

    else:
        start = jst_datetime(
            event["date"],
            event["start"],
        )

        end = jst_datetime(
            event["date"],
            event["end"],
        )

        if end <= start:
            end += timedelta(
                days=1
            )

    items = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=(
                start
                - timedelta(minutes=1)
            ).isoformat(),
            timeMax=(
                end
                + timedelta(minutes=1)
            ).isoformat(),
            singleEvents=True,
            maxResults=50,
        )
        .execute()
        .get(
            "items",
            [],
        )
    )

    target_title = (
        event["title"]
        .strip()
        .casefold()
    )

    for existing in items:
        existing_title = (
            existing
            .get(
                "summary",
                "",
            )
            .strip()
            .casefold()
        )

        if existing_title != target_title:
            continue

        if event["all_day"]:
            existing_date = (
                existing
                .get(
                    "start",
                    {},
                )
                .get(
                    "date"
                )
            )

            if (
                existing_date
                == event["date"]
            ):
                return True

        else:
            existing_start = (
                existing
                .get(
                    "start",
                    {},
                )
                .get(
                    "dateTime"
                )
            )

            if not existing_start:
                continue

            try:
                existing_dt = (
                    datetime
                    .fromisoformat(
                        existing_start
                    )
                )

                difference = abs(
                    (
                        existing_dt
                        - start
                    )
                    .total_seconds()
                )

                if difference <= 60:
                    return True

            except ValueError:
                pass

    return False


def insert_event(
    service,
    event,
):
    body = {
        "summary": (
            event["title"]
        ),
        "description": (
            event["description"]
        ),
    }

    if event["location"]:
        body["location"] = (
            event["location"]
        )

    parsed_day = (
        datetime.strptime(
            event["date"],
            "%Y-%m-%d",
        )
        .date()
    )

    if event["all_day"]:
        body["start"] = {
            "date": (
                parsed_day
                .isoformat()
            )
        }

        body["end"] = {
            "date": (
                (
                    parsed_day
                    + timedelta(days=1)
                )
                .isoformat()
            )
        }

    else:
        start = jst_datetime(
            event["date"],
            event["start"],
        )

        end = jst_datetime(
            event["date"],
            event["end"],
        )

        if end <= start:
            end += timedelta(
                days=1
            )

        body["start"] = {
            "dateTime": (
                start.isoformat()
            ),
            "timeZone": TZ_NAME,
        }

        body["end"] = {
            "dateTime": (
                end.isoformat()
            ),
            "timeZone": TZ_NAME,
        }

    return (
        service.events()
        .insert(
            calendarId="primary",
            body=body,
        )
        .execute()
    )


# ============================================================
# Main workflow
# ============================================================

def process(
    text: str,
):
    events = extract_events(
        text
    )

    if not events:
        raise RuntimeError(
            "予定を見つけられませんでした。\n\n"
            "例:\n"
            "Oct 19, 2026 11:59 PM UTC "
            "Submission deadline\n\n"
            "9月24日 14:00〜15:00 面談"
        )

    service = calendar_service()

    added = []
    skipped_duplicates = []
    manually_skipped = []
    auto_added = 0

    for index, event in enumerate(
        events,
        start=1,
    ):
        # ====================================================
        # 中間案
        # 明確なら自動登録
        # 曖昧なら確認画面
        # ====================================================

        if should_auto_add(
            event
        ):
            checked = {
                "title": event["title"],
                "date": event["date"],
                "start": event["start"],
                "end": event["end"],
                "all_day": event["all_day"],
                "location": event["location"],
                "description": event["description"],
            }

            auto_mode = True

        else:
            review = review_event(
                event,
                index,
                len(events),
            )

            if (
                review["action"]
                == "cancel"
            ):
                break

            if (
                review["action"]
                == "skip"
            ):
                manually_skipped.append(
                    event["title"]
                )

                continue

            checked = review[
                "event"
            ]

            auto_mode = False

        if is_duplicate(
            service,
            checked,
        ):
            skipped_duplicates.append(
                checked["title"]
            )

            continue

        created = insert_event(
            service,
            checked,
        )

        added.append(
            created.get(
                "summary",
                checked["title"],
            )
        )

        if auto_mode:
            auto_added += 1

    result = []

    if added:
        result.append(
            f"{len(added)}件追加しました"
        )

        if auto_added:
            result.append(
                f"自動追加: {auto_added}件"
            )

        for name in added:
            result.append(
                f"✓ {name}"
            )

    if skipped_duplicates:
        result.append("")
        result.append(
            f"{len(skipped_duplicates)}件は"
            "重複のためスキップしました"
        )

        for name in skipped_duplicates:
            result.append(
                f"= {name}"
            )

    if manually_skipped:
        result.append("")
        result.append(
            f"{len(manually_skipped)}件を"
            "手動でスキップしました"
        )

    if not result:
        result.append(
            "予定は追加されませんでした。"
        )

    return "\n".join(
        result
    )


# ============================================================
# Main
# ============================================================

def main():
    if (
        len(sys.argv) == 2
        and sys.argv[1] == "--auth"
    ):
        calendar_service()

        print(
            "Google Calendar "
            "authentication completed."
        )

        return

    if len(sys.argv) != 3:
        print(
            "Usage: add_calendar.py "
            "<input.txt> <result.txt>"
        )

        sys.exit(1)

    input_file = Path(
        sys.argv[1]
    )

    result_file = Path(
        sys.argv[2]
    )

    try:
        text = (
            input_file
            .read_text(
                encoding="utf-8-sig"
            )
            .strip()
        )

        if not text:
            raise ValueError(
                "クリップボードが空です。"
            )

        result = process(
            text
        )

        result_file.write_text(
            result,
            encoding="utf-8",
        )

    except Exception as error:
        result_file.write_text(
            "ERROR\n"
            f"{type(error).__name__}: "
            f"{error}",
            encoding="utf-8",
        )

        sys.exit(1)


if __name__ == "__main__":
    main()