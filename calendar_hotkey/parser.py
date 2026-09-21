from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import EventCandidate, ParserConfig, ValidationStatus

MONTHS = {name: i for i, names in enumerate(((), ("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"), ("may",), ("jun", "june"), ("jul", "july"), ("aug", "august"), ("sep", "sept", "september"), ("oct", "october"), ("nov", "november"), ("dec", "december"))) for name in names}
WEEKDAYS = {n: i for i, names in enumerate((("monday", "mon", "月"), ("tuesday", "tue", "tues", "火"), ("wednesday", "wed", "水"), ("thursday", "thu", "thur", "thurs", "木"), ("friday", "fri", "金"), ("saturday", "sat", "土"), ("sunday", "sun", "日"))) for n in names}
MONTH_PATTERN = "|".join(sorted(MONTHS, key=len, reverse=True))
WEEKDAY_PATTERN = "|".join(sorted((k for k in WEEKDAYS if len(k) > 1), key=len, reverse=True))
DATE_MARKER = re.compile(r"(?:20\d{2}[-/.年]\s*\d{1,2}|\d{1,2}\s*月\s*\d{1,2}\s*日|(?:" + MONTH_PATTERN + r")\s+\d{1,2}|\b(?:today|tomorrow|next\s+" + WEEKDAY_PATTERN + r"|this\s+" + WEEKDAY_PATTERN + r")\b|(?:今日|明日|明後日|今週|来週|再来週)|[月火水木金土日]曜(?:日)?)", re.I)


class ScheduleParser:
    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def parse(self, text: str, *, reference: datetime) -> list[EventCandidate]:
        if reference.tzinfo is None:
            raise ValueError("reference datetime must be timezone-aware")
        if not text or not text.strip():
            return []
        if len(text) > self.config.max_input_chars:
            raise ValueError(f"input exceeds {self.config.max_input_chars} characters")
        text = self._normalize(text)
        spans = self._event_spans(text)
        results = [self._parse_one(text[a:b].strip(), (a, b), reference) for a, b in spans]
        unique, seen = [], set()
        for item in results:
            key = (item.start, item.end, item.title.casefold(), item.source_span)
            if key not in seen:
                seen.add(key); unique.append(item)
        return unique[: self.config.max_events]

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("：", ":")
        return re.sub(r"\b([ap])\.?\s*m\.?\b", lambda m: m.group(1).upper() + "M", text, flags=re.I)

    def _event_spans(self, text: str) -> list[tuple[int, int]]:
        # Lines/sentences containing distinct date markers are independent events.
        chunks = [(m.start(), m.end()) for m in re.finditer(r"[^\n。！？!?.]+(?:[。！？!?.]|$)", text)]
        output = []
        for start, end in chunks:
            chunk = text[start:end]
            markers = list(DATE_MARKER.finditer(chunk))
            markers = [marker for i, marker in enumerate(markers) if i == 0 or marker.start() - markers[i - 1].end() > 2]
            if not markers:
                continue
            for i, marker in enumerate(markers):
                a = start + (0 if i == 0 else marker.start())
                b = start + (markers[i + 1].start() if i + 1 < len(markers) else len(chunk))
                output.append((a, b))
        return output

    def _parse_one(self, source: str, span: tuple[int, int], reference: datetime) -> EventCandidate:
        tz, label, explicit, tz_warning = self._timezone(source)
        local_ref = reference.astimezone(tz)
        day, date_warning, date_explicit = self._date(source, local_ref.date())
        start_clock, end_clock, duration, time_warning = self._times(source)
        missing, warnings = [], [x for x in (tz_warning, date_warning, time_warning) if x]
        start = end = None
        if day is None: missing.append("date")
        if start_clock is None: missing.append("start_time")
        if day and start_clock:
            start = datetime.combine(day, start_clock, tzinfo=tz)
            if end_clock:
                end = datetime.combine(day, end_clock, tzinfo=tz)
                if end <= start: end += timedelta(days=1)
            else:
                end = start + (duration or self.config.default_duration)
                warnings.append("end time inferred from configured default duration" if duration is None else "end time calculated from duration")
        title = self._title(source)
        if not title: missing.append("title"); title = ""
        # A missing explicit timezone is visible but normal local events may still auto-run.
        if not explicit: warnings.append(f"timezone not specified; assumed {label}")
        status = ValidationStatus.INVALID if missing else ValidationStatus.VALID
        if missing or date_warning or time_warning or (end_clock is None and duration is None): status = ValidationStatus.REVIEW if start else ValidationStatus.INVALID
        return EventCandidate(title, start, end, label, source, source, span, missing, warnings, explicit, status)

    def _date(self, text: str, today: date) -> tuple[date | None, str | None, bool]:
        m = re.search(r"(?<!\d)(20\d{2})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})(?:日)?", text)
        if m: return self._safe_date(*map(int, m.groups())), None, True
        m = re.search(r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
        if m: return self._infer(int(m[1]), int(m[2]), today), "year inferred", False
        m = re.search(rf"\b({MONTH_PATTERN})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(20\d{{2}}))?\b", text, re.I)
        if m:
            return (self._safe_date(int(m[3]), MONTHS[m[1].lower()], int(m[2])), None, True) if m[3] else (self._infer(MONTHS[m[1].lower()], int(m[2]), today), "year inferred", False)
        m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTH_PATTERN})(?:,?\s+(20\d{{2}}))?\b", text, re.I)
        if m:
            return (self._safe_date(int(m[3]), MONTHS[m[2].lower()], int(m[1])), None, True) if m[3] else (self._infer(MONTHS[m[2].lower()], int(m[1]), today), "year inferred", False)
        lower = text.lower()
        for word, delta in (("明後日", 2), ("day after tomorrow", 2), ("明日", 1), ("tomorrow", 1), ("今日", 0), ("本日", 0), ("today", 0)):
            if word in lower: return today + timedelta(days=delta), None, True
        m = re.search(r"(今週|来週|再来週)(?:の)?\s*([月火水木金土日])(?:曜(?:日)?)?", text)
        if m:
            monday = today - timedelta(days=today.weekday()); week = {"今週": 0, "来週": 1, "再来週": 2}[m[1]]
            return monday + timedelta(days=week * 7 + WEEKDAYS[m[2]]), None, True
        m = re.search(rf"\b(next|this)\s+({WEEKDAY_PATTERN})\b", lower)
        if m:
            target = WEEKDAYS[m[2]]; delta = (target - today.weekday()) % 7
            if m[1] == "next": delta = delta or 7
            return today + timedelta(days=delta), None, True
        m = re.search(r"([月火水木金土日])曜(?:日)?", text)
        if m:
            delta = (WEEKDAYS[m[1]] - today.weekday()) % 7 or 7
            return today + timedelta(days=delta), "weekday without week qualifier", False
        return None, None, False

    @staticmethod
    def _safe_date(year: int, month: int, day: int) -> date | None:
        try: return date(year, month, day)
        except ValueError: return None

    def _infer(self, month: int, day: int, today: date) -> date | None:
        value = self._safe_date(today.year, month, day)
        if value and value < today: value = self._safe_date(today.year + 1, month, day)
        return value

    def _times(self, text: str) -> tuple[time | None, time | None, timedelta | None, str | None]:
        jp = r"(?:(?:午前|午後)\s*)?\d{1,2}\s*時(?:\s*\d{1,2}\s*分)?(?!間)"
        en = r"(?:\d{1,2}(?::\d{2})?\s*(?:AM|PM)|\d{1,2}:\d{2}|noon|midnight)"
        m = re.search(rf"({jp})\s*(?:から|〜|～|~|-|–|—|to)\s*({jp})", text, re.I) or re.search(rf"(?:from\s*)?({en})\s*(?:-|–|—|to|until)\s*({en})", text, re.I)
        if m:
            a, b = self._clock(m[1]), self._clock(m[2]); return a, b, None, None if a and b else "invalid time range"
        token = re.search(jp, text, re.I) or re.search(rf"(?:\bat\s+)?({en})", text, re.I)
        raw = (token.group(1) if token.lastindex else token.group(0)) if token else ""
        start = self._clock(raw) if raw else None
        duration = None
        d = re.search(r"(\d+)\s*時間(?:\s*(半)|(\d+)\s*分)?|(?:for\s+)?(\d+)\s*(hours?|minutes?)", text, re.I)
        if d:
            if d[1]: duration = timedelta(hours=int(d[1]), minutes=30 if d[2] else int(d[3] or 0))
            else: duration = timedelta(**({"hours": int(d[4])} if d[5].lower().startswith("hour") else {"minutes": int(d[4])}))
        return start, None, duration, None

    @staticmethod
    def _clock(raw: str) -> time | None:
        raw = re.sub(r"\s+", "", raw).lower()
        if raw == "noon": return time(12)
        if raw == "midnight": return time(0)
        m = re.fullmatch(r"(?:(午前|午後))?(\d{1,2})時(?:(\d{1,2})分)?", raw)
        if m: ap, h, minute = m[1], int(m[2]), int(m[3] or 0)
        else:
            m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)?", raw)
            if not m: return None
            h, minute, ap = int(m[1]), int(m[2] or 0), m[3]
        if ap in ("午後", "pm") and h < 12: h += 12
        if ap in ("午前", "am") and h == 12: h = 0
        try: return time(h, minute)
        except ValueError: return None

    def _timezone(self, text: str) -> tuple[tzinfo, str, bool, str | None]:
        m = re.search(r"\b(?:UTC|GMT)\s*([+-])(\d{1,2})(?::?(\d{2}))?\b", text, re.I)
        if m:
            minutes = int(m[2]) * 60 + int(m[3] or 0)
            if minutes > 14 * 60: return self.config.timezone(), self.config.default_timezone, False, "invalid UTC offset"
            minutes *= 1 if m[1] == "+" else -1
            return timezone(timedelta(minutes=minutes)), f"UTC{m[1]}{int(m[2]):02d}:{int(m[3] or 0):02d}", True, None
        aliases = {"UTC": "UTC", "GMT": "UTC", "JST": "Asia/Tokyo", "ASIA/TOKYO": "Asia/Tokyo", "ASIA/BANGKOK": "Asia/Bangkok"}
        m = re.search(r"\b(Asia/Tokyo|Asia/Bangkok|UTC|GMT|JST)\b", text, re.I)
        if m:
            label = aliases[m[1].upper()]
            try: return ZoneInfo(label), label, True, None
            except ZoneInfoNotFoundError: pass
        return self.config.timezone(), self.config.default_timezone, False, None

    @staticmethod
    def _title(text: str) -> str:
        cleaned = DATE_MARKER.sub(" ", text)
        cleaned = re.sub(r"(?:(?:午前|午後)\s*)?\d{1,2}\s*時(?:\s*\d{1,2}\s*分)?|\b\d{1,2}(?::\d{2})?\s*(?:AM|PM)\b", " ", cleaned, flags=re.I)
        cleaned = re.sub(r"\b(?:at|from|to|for|UTC|GMT|JST|Asia/Tokyo|Asia/Bangkok)\b|\d+\s*(?:hours?|minutes?|時間|分)|(?:から|まで|〜|～)", " ", cleaned, flags=re.I)
        return re.sub(r"\s+", " ", cleaned).strip(" ,.:;-—–　")[:200]
