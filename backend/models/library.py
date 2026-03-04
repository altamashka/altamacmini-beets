"""Pydantic models for library, audit, and fix data."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TrackInfo(BaseModel):
    id: int
    title: str
    track: Optional[int] = None
    disc: Optional[int] = None
    length: Optional[float] = None
    path: str
    mb_trackid: Optional[str] = None
    format: Optional[str] = None
    bitrate: Optional[int] = None


class AlbumInfo(BaseModel):
    id: int
    album: str
    albumartist: str
    year: Optional[int] = None
    genre: Optional[str] = None
    mb_albumid: Optional[str] = None
    artpath: Optional[str] = None
    tracks: list[TrackInfo] = []


class AuditIssueType(str, Enum):
    duplicate_album = "duplicate_album"
    missing_artwork = "missing_artwork"
    missing_metadata = "missing_metadata"
    bad_track_numbers = "bad_track_numbers"
    split_album = "split_album"
    broken_file = "broken_file"


class AuditIssue(BaseModel):
    id: str
    type: AuditIssueType
    album_id: Optional[int] = None
    album_ids: Optional[list[int]] = None  # for duplicates / split albums
    description: str
    fixable: bool = True


class FixRequest(BaseModel):
    issue_ids: list[str]
    operation: str  # fetchart | fix_albumartist | fix_tracknums | unify_mbids | delete_duplicate
    params: dict = {}


class FixResult(BaseModel):
    issue_id: str
    success: bool
    message: str
