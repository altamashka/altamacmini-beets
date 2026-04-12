"""Shared dependencies for FastAPI routes.

The beets Library is opened once and reused across requests.
All beets operations must run in a ThreadPoolExecutor (beets is synchronous).
"""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from beets import config as beets_config
from beets.library import Library

from config import BEETS_CONFIG_PATH, BEETS_LIBRARY_PATH, MUSIC_ROOT

_executor = ThreadPoolExecutor(max_workers=4)
_lib_lock = threading.Lock()
_lib: Library | None = None


def get_executor() -> ThreadPoolExecutor:
    return _executor


def get_library() -> Library:
    """Return the shared beets Library instance, opening it if needed."""
    global _lib
    with _lib_lock:
        if _lib is None:
            beets_config.read(user=False, defaults=True)
            beets_config.set_file(BEETS_CONFIG_PATH)
            beets_config["directory"] = MUSIC_ROOT
            _lib = Library(BEETS_LIBRARY_PATH)
    return _lib


async def run_in_executor(fn, *args):
    """Run a synchronous beets function in the thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, fn, *args)
