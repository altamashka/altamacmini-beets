"""Audit runner — scans the beets library for issues.

Synchronous; runs in ThreadPoolExecutor. Emits audit_progress WS events
via ws_manager.broadcast_threadsafe() as issues are found.
"""
from __future__ import annotations

import logging
import os
import uuid
import asyncio
from collections import defaultdict

from deps import get_library
from models.library import AuditIssue, AuditIssueType
from models.websocket import WsEventType, WsMessage
from ws.manager import ws_manager

log = logging.getLogger(__name__)


def _decode(v) -> str:
    if v and isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return v or ""


def _emit(issues: list[AuditIssue], scan_id: str, loop: asyncio.AbstractEventLoop, issue: AuditIssue) -> None:
    issues.append(issue)
    ws_manager.broadcast_threadsafe(
        loop, scan_id,
        WsMessage.make(WsEventType.audit_progress, scan_id, issue=issue.model_dump()),
    )


def run_audit(scan_id: str, loop: asyncio.AbstractEventLoop) -> list[AuditIssue]:
    """Scan the entire beets library and return all detected issues."""
    lib = get_library()
    issues: list[AuditIssue] = []

    albums = list(lib.albums())
    log.info("[audit:%s] scanning %d albums", scan_id, len(albums))

    # Pre-compute groups for duplicate/split detection
    album_key_groups: dict[tuple, list[int]] = defaultdict(list)  # (album, albumartist) → [album_id]
    mbid_groups: dict[str, list[int]] = defaultdict(list)          # mb_albumid → [album_id]

    for album in albums:
        key = (_decode(album.album).lower().strip(), _decode(album.albumartist).lower().strip())
        album_key_groups[key].append(album.id)
        if album.mb_albumid:
            mbid_groups[_decode(album.mb_albumid)].append(album.id)

    album_by_id = {a.id: a for a in albums}

    # Per-album checks
    for album in albums:
        name = f"{_decode(album.albumartist)} – {_decode(album.album)}"
        items = list(album.items())

        # missing_artwork
        artpath = _decode(album.artpath)
        if not artpath or not os.path.isfile(artpath):
            _emit(issues, scan_id, loop, AuditIssue(
                id=str(uuid.uuid4()),
                type=AuditIssueType.missing_artwork,
                album_id=album.id,
                description=f"No artwork: {name}",
                fixable=True,
            ))

        # missing_metadata
        missing_fields = []
        if not _decode(album.albumartist).strip():
            missing_fields.append("albumartist")
        if not album.year or album.year == 0:
            missing_fields.append("year")
        if missing_fields:
            _emit(issues, scan_id, loop, AuditIssue(
                id=str(uuid.uuid4()),
                type=AuditIssueType.missing_metadata,
                album_id=album.id,
                description=f"Missing {', '.join(missing_fields)}: {name}",
                fixable="albumartist" in missing_fields,
            ))

        # bad_track_numbers
        bad_tracks = [i for i in items if not i.track or i.track == 0]
        if bad_tracks:
            _emit(issues, scan_id, loop, AuditIssue(
                id=str(uuid.uuid4()),
                type=AuditIssueType.bad_track_numbers,
                album_id=album.id,
                description=f"{len(bad_tracks)} track(s) missing track numbers: {name}",
                fixable=True,
            ))

        # broken_file
        for item in items:
            path = _decode(item.path)
            if not os.path.isfile(path):
                _emit(issues, scan_id, loop, AuditIssue(
                    id=str(uuid.uuid4()),
                    type=AuditIssueType.broken_file,
                    album_id=album.id,
                    description=f"File missing on disk: {os.path.basename(path)}",
                    fixable=False,
                ))

    # Duplicate albums (same album+albumartist, multiple beets Album records)
    seen_dup_keys: set[tuple] = set()
    for key, album_ids in album_key_groups.items():
        if len(album_ids) > 1:
            frozen = tuple(sorted(album_ids))
            if frozen in seen_dup_keys:
                continue
            seen_dup_keys.add(frozen)
            ref = album_by_id.get(album_ids[0])
            label = f"{_decode(ref.albumartist)} – {_decode(ref.album)}" if ref else str(key)
            _emit(issues, scan_id, loop, AuditIssue(
                id=str(uuid.uuid4()),
                type=AuditIssueType.duplicate_album,
                album_ids=album_ids,
                description=f"Duplicate: {label} ({len(album_ids)} copies)",
                fixable=True,
            ))

    # Split albums (same mb_albumid on multiple beets Album records)
    for mbid, album_ids in mbid_groups.items():
        if len(album_ids) > 1:
            _emit(issues, scan_id, loop, AuditIssue(
                id=str(uuid.uuid4()),
                type=AuditIssueType.split_album,
                album_ids=album_ids,
                description=f"Split album across {len(album_ids)} library entries (mb_albumid: {mbid})",
                fixable=True,
            ))

    log.info("[audit:%s] found %d issues", scan_id, len(issues))
    return issues
