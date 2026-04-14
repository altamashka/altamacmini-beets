"""Beets import session runner.

Runs in ThreadPoolExecutor. Bridges beets sync events to asyncio WS queue
via ImportBridge. Blocks on low-confidence matches via threading.Event.
"""
from __future__ import annotations

import logging
from typing import Optional

from beets import config as beets_config, importer
from beets.library import Library

from config import BEETS_CONFIG_PATH, BEETS_LIBRARY_PATH, MUSIC_ROOT
from ws.import_bridge import ImportBridge

LOW_CONFIDENCE = 0.90

log = logging.getLogger(__name__)


class BridgedImportSession(importer.ImportSession):
    """ImportSession subclass that intercepts match choices and bridges to WS."""

    def __init__(
        self,
        lib: Library,
        loghandler,
        paths: list[str],
        query,
        bridge: ImportBridge,
    ):
        super().__init__(lib, loghandler, paths, query)
        self.bridge = bridge
        self._imported_count = 0
        self._skipped_count = 0

    def choose_match(self, task):
        """Called by beets for each album task. May block for user decision."""
        album_path = str(task.paths[0]) if task.paths else ""
        self.bridge.on_album_begin(album_path)

        candidates = task.candidates
        if not candidates:
            self.bridge.on_album_skipped("no candidates")
            self._skipped_count += 1
            return importer.action.SKIP

        best = candidates[0]
        # beets Distance: 0.0 = perfect match, 1.0 = worst — invert for display
        confidence = 1.0 - best.distance.distance

        before = _item_metadata(task)
        after = _match_metadata(best.info)

        self.bridge.on_album_match(
            confidence=confidence,
            before=before,
            after=after,
            artwork={"found": False},
            tracks=_track_list(best),
        )

        if confidence >= LOW_CONFIDENCE:
            self.bridge.on_album_applying()
            self._imported_count += 1
            return best

        decision = self.bridge.on_decision_needed(
            confidence=confidence,
            before=before,
            after=after,
            candidates=[_candidate_info(c) for c in candidates[:5]],
        )

        if decision == "apply":
            self.bridge.on_album_applying()
            self._imported_count += 1
            return best
        elif decision == "as_is":
            self.bridge.on_album_applying()
            self._imported_count += 1
            return importer.action.ASIS
        else:
            self.bridge.on_album_skipped("user skipped")
            self._skipped_count += 1
            return importer.action.SKIP

    def choose_item(self, task):
        """For single-track imports — auto-apply best match."""
        if task.candidates:
            self._imported_count += 1
            return task.candidates[0]
        self._skipped_count += 1
        return importer.action.SKIP

    def resolve_duplicates(self, task, found_duplicates):
        """Skip duplicates conservatively."""
        self._skipped_count += 1
        return importer.action.SKIP


def _item_metadata(task) -> dict:
    items = list(task.items) if hasattr(task, "items") else []
    if not items:
        return {}
    item = items[0]
    return {
        "artist": getattr(item, "artist", "") or "",
        "album": getattr(item, "album", "") or "",
        "albumartist": getattr(item, "albumartist", "") or "",
        "year": getattr(item, "year", None),
        "genre": getattr(item, "genre", "") or "",
    }


def _match_metadata(info) -> dict:
    return {
        "artist": getattr(info, "artist", "") or "",
        "album": getattr(info, "album", "") or "",
        "albumartist": getattr(info, "albumartist", "") or "",
        "year": getattr(info, "year", None),
        "genre": "",
    }


def _track_list(match) -> list[dict]:
    """Build a compact track list from a match's mapping."""
    try:
        tracks = []
        for item, track_info in match.mapping.items():
            tracks.append({
                "track": getattr(track_info, "index", None),
                "title": getattr(track_info, "title", "") or "",
                "current_title": getattr(item, "title", "") or "",
            })
        return tracks
    except Exception:
        return []


def _candidate_info(candidate) -> dict:
    info = candidate.info
    return {
        "artist": getattr(info, "artist", "") or "",
        "album": getattr(info, "album", "") or "",
        "year": getattr(info, "year", None),
        "mb_albumid": getattr(info, "album_id", "") or "",
        "distance": candidate.distance.distance,
        "confidence": 1.0 - candidate.distance.distance,
    }


def run_import(job_id: str, paths: list[str], bridge: ImportBridge) -> dict:
    """Run beets import synchronously. Call this in ThreadPoolExecutor.

    Returns stats dict: {albums_imported, albums_skipped, albums_error}
    """
    stats = {"albums_imported": 0, "albums_skipped": 0, "albums_error": 0}

    try:
        beets_config.read(user=False, defaults=True)
        beets_config.set_file(BEETS_CONFIG_PATH)

        beets_config["import"]["timid"] = False
        beets_config["import"]["copy"] = False
        beets_config["import"]["move"] = True
        beets_config["import"]["write"] = True
        beets_config["import"]["autotag"] = True
        beets_config["import"]["quiet"] = False

        # Override directory to match container mount path
        beets_config["directory"] = MUSIC_ROOT

        lib = Library(BEETS_LIBRARY_PATH)
        try:
            session = BridgedImportSession(
                lib=lib,
                loghandler=None,
                paths=paths,
                query=None,
                bridge=bridge,
            )
            session.run()
            stats["albums_imported"] = session._imported_count
            stats["albums_skipped"] = session._skipped_count
            bridge.on_import_complete(stats)
        finally:
            lib._close()
    except Exception as e:
        log.exception("beets import failed for job %s", job_id)
        bridge.on_import_error(str(e))
        stats["albums_error"] += 1

    return stats
