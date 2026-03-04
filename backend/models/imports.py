"""Pydantic models for the import pipeline."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ImportJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    waiting_decision = "waiting_decision"
    complete = "complete"
    error = "error"


class ImportRequest(BaseModel):
    paths: list[str]  # relative to DOWNLOADS_ROOT or absolute


class ManualDecision(str, Enum):
    apply = "apply"
    skip = "skip"
    as_is = "as_is"
    search = "search"


class DecisionRequest(BaseModel):
    decision: ManualDecision
    search_query: Optional[str] = None  # only if decision == "search"


class AlbumMatchPayload(BaseModel):
    confidence: float
    before: dict
    after: dict
    artwork: dict
    tracks: list[dict] = []


class ImportJob(BaseModel):
    id: str
    status: ImportJobStatus
    paths: list[str]
    albums_total: int = 0
    albums_done: int = 0
    albums_skipped: int = 0
    current_album: Optional[str] = None
    pending_decision: Optional[AlbumMatchPayload] = None
    error: Optional[str] = None
