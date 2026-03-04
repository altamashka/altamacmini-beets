"""Beets fix operations — Phase 3 stubs.

Each function runs synchronously in ThreadPoolExecutor.
They will emit WS events via a FixBridge (to be implemented in Phase 3).
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def fetchart(album_id: int) -> dict:
    """Fetch and embed cover art for the given album.

    Uses beets fetchart plugin to find art from online sources or embedded tags.
    Returns: {ok: bool, source: str | None, error: str | None}
    """
    raise NotImplementedError("Phase 3")


def fix_albumartist(album_id: int) -> dict:
    """Set albumartist field from MusicBrainz or infer from track artists.

    Returns: {ok: bool, old_value: str, new_value: str, error: str | None}
    """
    raise NotImplementedError("Phase 3")


def fix_tracknums(album_id: int) -> dict:
    """Renumber tracks sequentially based on disc/track position.

    Returns: {ok: bool, fixed_count: int, error: str | None}
    """
    raise NotImplementedError("Phase 3")


def unify_mbids(album_id: int) -> dict:
    """Ensure all tracks in the album share the same MusicBrainz album ID.

    Returns: {ok: bool, updated_count: int, error: str | None}
    """
    raise NotImplementedError("Phase 3")


def delete_album(album_id: int) -> dict:
    """Remove album from beets library and delete files from disk.

    Returns: {ok: bool, deleted_files: list[str], error: str | None}
    """
    raise NotImplementedError("Phase 3")
