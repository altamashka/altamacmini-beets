"""WebSocket message models."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_serializer


class WsEventType(str, Enum):
    # Import events
    import_started = "import_started"
    album_begin = "album_begin"
    album_match = "album_match"
    album_decision_needed = "album_decision_needed"
    album_applying = "album_applying"
    album_complete = "album_complete"
    album_skipped = "album_skipped"
    import_complete = "import_complete"
    import_error = "import_error"

    # Fix events
    fix_started = "fix_started"
    fix_progress = "fix_progress"
    fix_complete = "fix_complete"
    fix_error = "fix_error"

    # Audit events
    audit_started = "audit_started"
    audit_progress = "audit_progress"
    audit_complete = "audit_complete"


class WsMessage(BaseModel):
    event: WsEventType
    job_id: str
    timestamp: datetime
    payload: dict[str, Any] = {}

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime) -> str:
        return v.isoformat()

    @classmethod
    def make(cls, event: WsEventType, job_id: str, **payload) -> "WsMessage":
        return cls(
            event=event,
            job_id=job_id,
            timestamp=datetime.now(timezone.utc),
            payload=payload,
        )
