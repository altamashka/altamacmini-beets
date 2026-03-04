"""Read-only beets Library queries.

All functions are synchronous and intended to run in ThreadPoolExecutor.
"""
from __future__ import annotations

import os

from beets.library import Library

from config import BEETS_LIBRARY_PATH, MUSIC_ROOT
from models.library import AlbumInfo, TrackInfo


def _track_from_item(item) -> TrackInfo:
    path = item.path.decode() if isinstance(item.path, bytes) else item.path
    return TrackInfo(
        id=item.id,
        title=item.title or "",
        track=item.track or None,
        disc=item.disc or None,
        length=item.length or None,
        path=path,
        mb_trackid=item.mb_trackid or None,
        format=item.format or None,
        bitrate=item.bitrate or None,
    )


def _album_from_album(album, include_tracks: bool = False) -> AlbumInfo:
    artpath = album.artpath
    if artpath and isinstance(artpath, bytes):
        artpath = artpath.decode()
    return AlbumInfo(
        id=album.id,
        album=album.album or "",
        albumartist=album.albumartist or "",
        year=album.year or None,
        genre=album.genre or None,
        mb_albumid=album.mb_albumid or None,
        artpath=artpath or None,
        tracks=[_track_from_item(i) for i in album.items()] if include_tracks else [],
    )


def list_albums(query: str = "") -> list[AlbumInfo]:
    with Library(BEETS_LIBRARY_PATH) as lib:
        albums = lib.albums(query or "")
        return [_album_from_album(a) for a in albums]


def get_album(album_id: int) -> AlbumInfo | None:
    with Library(BEETS_LIBRARY_PATH) as lib:
        album = lib.get_album(album_id)
        if album is None:
            return None
        return _album_from_album(album, include_tracks=True)


def library_stats() -> dict:
    with Library(BEETS_LIBRARY_PATH) as lib:
        albums = list(lib.albums())
        items = list(lib.items())
        return {
            "album_count": len(albums),
            "track_count": len(items),
        }


def is_library_connected() -> bool:
    try:
        with Library(BEETS_LIBRARY_PATH) as lib:
            list(lib.albums(""))
            return True
    except Exception:
        return False
