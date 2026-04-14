"""Filesystem browser for the downloads directory.

Synchronous — run in ThreadPoolExecutor.
"""
from __future__ import annotations

import os
from pathlib import Path

from config import DOWNLOADS_ROOT

AUDIO_EXTENSIONS = {".flac", ".mp3", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".wma", ".alac", ".aiff"}


def count_audio_files(path: str) -> int:
    """Recursively count audio files under path. Returns 0 if path missing."""
    p = Path(path)
    if not p.exists():
        return 0
    if p.is_file():
        return 1 if p.suffix.lower() in AUDIO_EXTENSIONS else 0
    count = 0
    for entry in p.rglob("*"):
        if entry.is_file() and entry.suffix.lower() in AUDIO_EXTENSIONS:
            count += 1
    return count


def list_downloads(subpath: str = "") -> dict:
    """Return directory tree node for the given subpath under DOWNLOADS_ROOT."""
    root = Path(DOWNLOADS_ROOT)
    target = (root / subpath.lstrip("/")).resolve()

    # Prevent path traversal
    if not str(target).startswith(str(root)):
        raise PermissionError("Path outside downloads root")

    if not target.exists():
        raise FileNotFoundError(f"Path not found: {subpath}")

    entries = []
    if target.is_dir():
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name.lower())):
            rel = str(entry.relative_to(root))
            entries.append({
                "name": entry.name,
                "path": rel,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else None,
            })

    return {
        "path": str(target.relative_to(root)) if target != root else "",
        "is_dir": target.is_dir(),
        "entries": entries,
    }


def resolve_import_paths(paths: list[str]) -> list[str]:
    """Convert relative paths (under DOWNLOADS_ROOT) to absolute paths."""
    root = Path(DOWNLOADS_ROOT)
    result = []
    for p in paths:
        if os.path.isabs(p):
            abs_path = Path(p).resolve()
        else:
            abs_path = (root / p).resolve()
        if not str(abs_path).startswith(str(root)):
            raise PermissionError(f"Path outside downloads root: {p}")
        result.append(str(abs_path))
    return result
