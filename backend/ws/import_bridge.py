"""Bridge between beets synchronous events and the asyncio WebSocket queue.

The import session runs in a ThreadPoolExecutor. beets fires callbacks on the
beets thread. This module translates those callbacks into WsMessage objects
and enqueues them thread-safely onto the asyncio event loop.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Callable, Optional

from models.websocket import WsEventType, WsMessage
from ws.manager import ws_manager


class ImportBridge:
    """Plugs into beets session hooks to bridge events to asyncio."""

    LOW_CONFIDENCE_THRESHOLD = 0.90

    def __init__(self, job_id: str, loop: asyncio.AbstractEventLoop):
        self.job_id = job_id
        self.loop = loop
        self._decision_event: Optional[threading.Event] = None
        self._decision_value: Optional[str] = None  # "apply" | "skip" | "as_is"

    def _emit(self, event: WsEventType, **payload) -> None:
        msg = WsMessage.make(event, self.job_id, **payload)
        ws_manager.broadcast_threadsafe(self.loop, self.job_id, msg)

    # --- beets event handlers (called from beets thread) ---

    def on_album_begin(self, album_path: str) -> None:
        self._emit(WsEventType.album_begin, path=album_path)

    def on_album_match(self, confidence: float, before: dict, after: dict, artwork: dict, tracks: list) -> None:
        self._emit(
            WsEventType.album_match,
            confidence=confidence,
            before=before,
            after=after,
            artwork=artwork,
            tracks=tracks,
        )

    def on_decision_needed(
        self,
        confidence: float,
        before: dict,
        after: dict,
        candidates: list,
    ) -> str:
        """Block the beets thread until the user makes a decision."""
        self._decision_event = threading.Event()
        self._decision_value = None

        self._emit(
            WsEventType.album_decision_needed,
            confidence=confidence,
            before=before,
            after=after,
            candidates=candidates,
        )

        # Block beets thread until POST /api/import/jobs/{id}/decide arrives
        self._decision_event.wait()
        return self._decision_value or "skip"

    def resolve_decision(self, decision: str) -> None:
        """Called from the asyncio thread (HTTP handler) to unblock beets."""
        self._decision_value = decision
        if self._decision_event:
            self._decision_event.set()

    def on_album_applying(self) -> None:
        self._emit(WsEventType.album_applying)

    def on_album_complete(self, dest_path: str) -> None:
        self._emit(WsEventType.album_complete, dest_path=dest_path)

    def on_album_skipped(self, reason: str) -> None:
        self._emit(WsEventType.album_skipped, reason=reason)

    def on_import_complete(self, stats: dict) -> None:
        self._emit(WsEventType.import_complete, **stats)

    def on_import_error(self, error: str) -> None:
        self._emit(WsEventType.import_error, error=error)
