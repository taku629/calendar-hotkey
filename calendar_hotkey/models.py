from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo


class ValidationStatus(str, Enum):
    VALID = "valid"
    REVIEW = "review"
    INVALID = "invalid"


@dataclass(frozen=True)
class ParserConfig:
    default_timezone: str = "Asia/Tokyo"
    default_duration: timedelta = timedelta(hours=1)
    locale: str = "auto"
    max_input_chars: int = 100_000
    max_events: int = 50

    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.default_timezone)


@dataclass
class EventCandidate:
    title: str
    start: datetime | None
    end: datetime | None
    timezone: str
    description: str
    source_text: str
    source_span: tuple[int, int]
    missing_information: list[str] = field(default_factory=list)
    ambiguity_warnings: list[str] = field(default_factory=list)
    timezone_explicit: bool = False
    validation_status: ValidationStatus = ValidationStatus.REVIEW

    @property
    def can_auto_create(self) -> bool:
        return self.validation_status is ValidationStatus.VALID

    def as_calendar_body(self) -> dict:
        if not self.start or not self.end or not self.title.strip():
            raise ValueError("candidate is not complete")
        return {
            "summary": self.title,
            "description": self.description,
            "start": {"dateTime": self.start.isoformat(), "timeZone": self.timezone},
            "end": {"dateTime": self.end.isoformat(), "timeZone": self.timezone},
        }
