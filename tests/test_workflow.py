from datetime import datetime
from zoneinfo import ZoneInfo

from add_calendar import process

REF = datetime(2026, 9, 21, 12, tzinfo=ZoneInfo("Asia/Tokyo"))


class NeverCalledService:
    def events(self):
        raise AssertionError("ambiguous input must not access Google Calendar")


def test_auto_mode_stops_ambiguous_candidate_before_api():
    result = process("2026-10-22 14時 面談", mode="AUTO", service=NeverCalledService(), reference=REF)
    assert "確認が必要" in result


def test_review_cancellation_stops_before_api():
    result = process("2026-10-22 14時から16時 面談", mode="REVIEW", service=NeverCalledService(), reference=REF, confirmer=lambda _: False)
    assert result == "予定は追加されませんでした。"


def test_bad_mode_is_rejected():
    try:
        process("tomorrow at 2 PM meeting", mode="unsafe", reference=REF)
    except ValueError as exc:
        assert "AUTO or REVIEW" in str(exc)
    else:
        raise AssertionError("invalid mode accepted")
