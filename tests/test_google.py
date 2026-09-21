from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from calendar_hotkey.google import GoogleCalendarGateway
from calendar_hotkey.models import EventCandidate, ValidationStatus


class Request:
    def __init__(self, value=None, error=None): self.value, self.error = value, error
    def execute(self, **kwargs):
        if self.error: raise self.error
        return self.value


class Events:
    def __init__(self, listed=None, insert_error=None): self.listed, self.insert_error = listed or [], insert_error
    def list(self, **kwargs): return Request({"items": self.listed})
    def insert(self, **kwargs): return Request({"id": "new-id"}, self.insert_error)


class Service:
    def __init__(self, events): self._events = events
    def events(self): return self._events


def candidate(title="Meeting"):
    start = datetime(2026, 10, 22, 14, tzinfo=ZoneInfo("Asia/Tokyo"))
    return EventCandidate(title, start, start + timedelta(hours=1), "Asia/Tokyo", "source", "source", (0, 6), validation_status=ValidationStatus.VALID)


def test_create_and_duplicate_prevention():
    event = candidate()
    assert GoogleCalendarGateway(Service(Events())).create(event).status == "created"
    existing = {"summary": "meeting", "start": {"dateTime": event.start.isoformat()}}
    assert GoogleCalendarGateway(Service(Events([existing]))).create(event).status == "duplicate"


def test_partial_batch_failure_is_recoverable():
    gateway = GoogleCalendarGateway(Service(Events(insert_error=TimeoutError("timeout"))))
    results = gateway.create_batch([candidate("one"), candidate("two")])
    assert [r.status for r in results] == ["failed", "failed"]
    assert all("timeout" in r.error for r in results)


def test_review_candidate_never_calls_api():
    item = candidate(); item.validation_status = ValidationStatus.REVIEW
    assert GoogleCalendarGateway(Service(Events())).create(item).status == "review_required"
    assert GoogleCalendarGateway(Service(Events())).create(item, confirmed=True).status == "created"
