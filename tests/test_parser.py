from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from calendar_hotkey import ParserConfig, ScheduleParser, ValidationStatus

REF = datetime(2026, 9, 21, 12, tzinfo=ZoneInfo("Asia/Tokyo"))  # Monday


@pytest.mark.parametrize(("text", "day", "hour", "minute"), [
    ("明日の14時から16時 面談", "2026-09-22", 14, 0),
    ("明後日 午後3時 研究相談", "2026-09-23", 15, 0),
    ("来週の水曜日15時からオンラインミーティング", "2026-09-30", 15, 0),
    ("今週金曜日 15時30分 レビュー", "2026-09-25", 15, 30),
    ("2026年10月22日 午後3時 面談", "2026-10-22", 15, 0),
    ("tomorrow at 3 PM Meeting", "2026-09-22", 15, 0),
    ("next Wednesday at 3:30 PM Meeting", "2026-09-23", 15, 30),
    ("October 22, 2026 at 11:59 PM UTC Submit entry", "2026-10-22", 23, 59),
])
def test_dates_and_times(text, day, hour, minute):
    event = ScheduleParser().parse(text, reference=REF)[0]
    assert event.start.date().isoformat() == day
    assert (event.start.hour, event.start.minute) == (hour, minute)


def test_duration_and_cross_midnight():
    parser = ScheduleParser()
    duration = parser.parse("明日 14時から1時間半 大学の面談", reference=REF)[0]
    assert duration.end - duration.start == timedelta(minutes=90)
    overnight = parser.parse("2026年10月22日 23時から1時 夜間作業", reference=REF)[0]
    assert overnight.end.date().isoformat() == "2026-10-23"


def test_multiple_events_have_independent_source_spans():
    text = "September 24, 3 PM: University meeting.\nSeptember 25, 10 AM: Research discussion.\nSeptember 26, 8 PM: Weekly review."
    events = ScheduleParser().parse(text, reference=REF)
    assert [event.title for event in events] == ["University meeting", "Research discussion", "Weekly review"]
    assert len({event.source_span for event in events}) == 3
    assert all(event.source_text in text for event in events)


def test_explicit_utc_is_not_converted_or_relabelled():
    event = ScheduleParser().parse("October 22, 2026 at 11:59 PM UTC Submit", reference=REF)[0]
    assert event.timezone == "UTC"
    assert event.start.utcoffset() == timedelta(0)
    assert event.timezone_explicit


def test_default_bangkok_and_reference_near_midnight():
    config = ParserConfig(default_timezone="Asia/Bangkok")
    reference = datetime(2026, 12, 31, 23, 55, tzinfo=ZoneInfo("Asia/Bangkok"))
    event = ScheduleParser(config).parse("tomorrow at 1 AM New year task", reference=reference)[0]
    assert event.start.isoformat().startswith("2027-01-01T01:00")
    assert "assumed Asia/Bangkok" in event.ambiguity_warnings[-1]


def test_offset_and_leap_year():
    event = ScheduleParser().parse("2028-02-29 at 23:30 UTC+07:00 Leap review", reference=REF)[0]
    assert event.start.utcoffset() == timedelta(hours=7)
    assert event.start.day == 29


@pytest.mark.parametrize("text", ["", "nothing schedulable", "2026-02-29 at 2 PM invalid"])
def test_empty_missing_or_invalid_date_is_safe(text):
    events = ScheduleParser().parse(text, reference=REF)
    assert not events or events[0].validation_status is not ValidationStatus.VALID


def test_ambiguous_weekday_and_missing_time_require_review():
    ambiguous = ScheduleParser().parse("水曜日 14時 打合せ", reference=REF)[0]
    assert ambiguous.validation_status is ValidationStatus.REVIEW
    missing = ScheduleParser().parse("October 22, 2026 Submit", reference=REF)[0]
    assert missing.validation_status is ValidationStatus.INVALID
    assert "start_time" in missing.missing_information


def test_default_duration_requires_review_but_explicit_range_is_valid():
    inferred = ScheduleParser().parse("2026-10-22 14時 面談", reference=REF)[0]
    explicit = ScheduleParser().parse("2026-10-22 14時から16時 面談", reference=REF)[0]
    assert inferred.validation_status is ValidationStatus.REVIEW
    assert explicit.validation_status is ValidationStatus.VALID


def test_limits_long_input():
    parser = ScheduleParser(ParserConfig(max_input_chars=20))
    with pytest.raises(ValueError, match="exceeds"):
        parser.parse("x" * 21, reference=REF)


def test_reference_must_be_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        ScheduleParser().parse("tomorrow at 2 PM", reference=datetime(2026, 1, 1))
