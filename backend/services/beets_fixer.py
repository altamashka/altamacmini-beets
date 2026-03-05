"""Beets fix operations — Phase 3.

Each function runs synchronously in ThreadPoolExecutor.
Uses the shared Library singleton from deps.get_library().
"""
from __future__ import annotations

import logging
import os
from collections import Counter

import httpx
import mutagen

from deps import get_library

log = logging.getLogger(__name__)


def _decode(v) -> str:
    if v and isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return v or ""


def fetchart(album_id: int) -> dict:
    """Fetch and embed cover art for the given album.

    Tries (in order): existing valid artpath, embedded tags, Cover Art Archive.
    Returns: {ok: bool, source: str | None, error: str | None}
    """
    lib = get_library()
    album = lib.get_album(album_id)
    if album is None:
        return {"ok": False, "source": None, "error": "Album not found"}

    # Already has valid art
    artpath = _decode(album.artpath)
    if artpath and os.path.isfile(artpath):
        return {"ok": True, "source": "existing", "error": None}

    items = list(album.items())
    if not items:
        return {"ok": False, "source": None, "error": "No tracks in album"}

    first_item_path = _decode(items[0].path)
    album_dir = os.path.dirname(first_item_path)

    # Try embedded art from track files
    for item in items:
        path = _decode(item.path)
        if not os.path.isfile(path):
            continue
        try:
            tags = mutagen.File(path)
            if tags is None:
                continue
            pic_data: bytes | None = None
            # FLAC: has .pictures attribute
            if hasattr(tags, "pictures") and tags.pictures:
                pic_data = tags.pictures[0].data
            # ID3 (MP3 etc): APIC frames
            if pic_data is None:
                for key in tags.keys():
                    if key.startswith("APIC"):
                        pic_data = tags[key].data
                        break
            if pic_data:
                out_path = os.path.join(album_dir, "cover.jpg")
                with open(out_path, "wb") as f:
                    f.write(pic_data)
                album.artpath = out_path
                album.store()
                return {"ok": True, "source": "embedded", "error": None}
        except Exception:
            continue

    # Try Cover Art Archive
    mb_albumid = _decode(album.mb_albumid)
    if mb_albumid:
        try:
            url = f"https://coverartarchive.org/release/{mb_albumid}/front"
            resp = httpx.get(url, follow_redirects=True, timeout=10)
            if resp.status_code == 200:
                out_path = os.path.join(album_dir, "cover.jpg")
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                album.artpath = out_path
                album.store()
                return {"ok": True, "source": "coverartarchive", "error": None}
        except Exception as e:
            return {"ok": False, "source": None, "error": f"Cover Art Archive failed: {e}"}

    return {"ok": False, "source": None, "error": "No art source found"}


def fix_albumartist(album_id: int) -> dict:
    """Set albumartist field inferred from track artists.

    Returns: {ok: bool, old_value: str, new_value: str, error: str | None}
    """
    lib = get_library()
    album = lib.get_album(album_id)
    if album is None:
        return {"ok": False, "old_value": "", "new_value": "", "error": "Album not found"}

    old_value = _decode(album.albumartist)
    items = list(album.items())
    if not items:
        return {"ok": False, "old_value": old_value, "new_value": "", "error": "No tracks in album"}

    artist_counts = Counter(_decode(i.artist) for i in items if i.artist)
    if not artist_counts:
        return {"ok": False, "old_value": old_value, "new_value": "", "error": "No track artists found"}

    if len(artist_counts) == 1:
        new_value = artist_counts.most_common(1)[0][0]
    elif len(artist_counts) <= 3:
        new_value = artist_counts.most_common(1)[0][0]
    else:
        new_value = "Various Artists"

    album.albumartist = new_value
    album.store()
    for item in items:
        item.albumartist = new_value
        item.store()

    return {"ok": True, "old_value": old_value, "new_value": new_value, "error": None}


def fix_tracknums(album_id: int) -> dict:
    """Renumber tracks sequentially based on disc/track position.

    Returns: {ok: bool, fixed_count: int, error: str | None}
    """
    lib = get_library()
    album = lib.get_album(album_id)
    if album is None:
        return {"ok": False, "fixed_count": 0, "error": "Album not found"}

    items = sorted(album.items(), key=lambda i: (i.disc or 1, i.track or 9999, _decode(i.title)))
    for idx, item in enumerate(items, start=1):
        item.track = idx
        item.store()

    return {"ok": True, "fixed_count": len(items), "error": None}


def unify_mbids(album_id: int) -> dict:
    """Ensure all tracks share the album's MusicBrainz album ID.

    Returns: {ok: bool, updated_count: int, error: str | None}
    """
    lib = get_library()
    album = lib.get_album(album_id)
    if album is None:
        return {"ok": False, "updated_count": 0, "error": "Album not found"}

    mb_albumid = _decode(album.mb_albumid)
    if not mb_albumid:
        return {"ok": False, "updated_count": 0, "error": "Album has no mb_albumid"}

    count = 0
    for item in album.items():
        if _decode(item.mb_albumid) != mb_albumid:
            item.mb_albumid = mb_albumid
            item.store()
            count += 1

    return {"ok": True, "updated_count": count, "error": None}


def delete_album(album_id: int) -> dict:
    """Remove album from beets library and delete files from disk.

    Returns: {ok: bool, deleted_files: list[str], error: str | None}
    """
    lib = get_library()
    album = lib.get_album(album_id)
    if album is None:
        return {"ok": False, "deleted_files": [], "error": "Album not found"}

    deleted_files: list[str] = []
    for item in list(album.items()):
        path = _decode(item.path)
        if os.path.isfile(path):
            try:
                os.remove(path)
                deleted_files.append(path)
            except Exception as e:
                log.warning("Failed to delete %s: %s", path, e)
        item.remove()

    # Remove artwork file if it exists
    artpath = _decode(album.artpath)
    if artpath and os.path.isfile(artpath):
        try:
            os.remove(artpath)
        except Exception:
            pass

    album.remove()
    return {"ok": True, "deleted_files": deleted_files, "error": None}
