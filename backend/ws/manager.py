"""Per-job asyncio.Queue registry for WebSocket connections."""
from __future__ import annotations

import asyncio
from collections import defaultdict

from models.websocket import WsMessage


class ConnectionManager:
    """Manages per-job queues for broadcasting WS events."""

    def __init__(self):
        # job_id → list of asyncio.Queue
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue[WsMessage | None] = asyncio.Queue()
        self._queues[job_id].append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        try:
            self._queues[job_id].remove(q)
        except ValueError:
            pass
        if not self._queues[job_id]:
            del self._queues[job_id]

    async def broadcast(self, job_id: str, message: WsMessage) -> None:
        for q in list(self._queues.get(job_id, [])):
            await q.put(message)

    def broadcast_threadsafe(self, loop: asyncio.AbstractEventLoop, job_id: str, message: WsMessage) -> None:
        """Called from a non-async thread to enqueue a message."""
        asyncio.run_coroutine_threadsafe(self.broadcast(job_id, message), loop)

    async def close_job(self, job_id: str) -> None:
        """Signal all subscribers that the stream is done (None sentinel)."""
        for q in list(self._queues.get(job_id, [])):
            await q.put(None)


ws_manager = ConnectionManager()
