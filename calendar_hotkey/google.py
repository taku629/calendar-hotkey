from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Iterable

from .models import EventCandidate


class CalendarOperationError(RuntimeError):
    """A structured, user-safe Google Calendar operation failure."""


@dataclass
class CreationResult:
    candidate: EventCandidate
    status: str
    event_id: str | None = None
    error: str | None = None


class GoogleCalendarGateway:
    def __init__(self, service, *, calendar_id: str = "primary"):
        self.service, self.calendar_id = service, calendar_id

    def is_duplicate(self, candidate: EventCandidate) -> bool:
        if not candidate.start or not candidate.end: return False
        try:
            items = self.service.events().list(calendarId=self.calendar_id, timeMin=(candidate.start - timedelta(minutes=1)).isoformat(), timeMax=(candidate.end + timedelta(minutes=1)).isoformat(), singleEvents=True, maxResults=50).execute(num_retries=2).get("items", [])
        except Exception as exc:
            raise CalendarOperationError(f"duplicate check failed: {exc}") from exc
        return any(i.get("summary", "").strip().casefold() == candidate.title.strip().casefold() and i.get("start", {}).get("dateTime") == candidate.start.isoformat() for i in items)

    def create(self, candidate: EventCandidate, *, confirmed: bool = False) -> CreationResult:
        if (candidate.missing_information or not candidate.start or not candidate.end):
            return CreationResult(candidate, "invalid")
        if not candidate.can_auto_create and not confirmed: return CreationResult(candidate, "review_required")
        try:
            if self.is_duplicate(candidate): return CreationResult(candidate, "duplicate")
            created = self.service.events().insert(calendarId=self.calendar_id, body=candidate.as_calendar_body()).execute(num_retries=2)
            return CreationResult(candidate, "created", created.get("id"))
        except Exception as exc:
            return CreationResult(candidate, "failed", error=str(exc))

    def create_batch(self, candidates: Iterable[EventCandidate], *, confirmed: bool = False) -> list[CreationResult]:
        # Deliberately sequential: each result survives a partial batch failure.
        return [self.create(candidate, confirmed=confirmed) for candidate in candidates]
