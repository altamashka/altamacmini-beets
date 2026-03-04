"""Fix operation endpoints + WebSocket stream.

Phase 3 implementation — stubs here, full logic in services/beets_fixer.py.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.library import FixRequest, FixResult
from models.websocket import WsEventType, WsMessage
from ws.manager import ws_manager

router = APIRouter(prefix="/api/fix", tags=["fixes"])

_fix_jobs: dict[str, dict] = {}


@router.post("/", response_model=dict, status_code=201)
async def start_fix(request: FixRequest):
    fix_id = str(uuid.uuid4())
    _fix_jobs[fix_id] = {"id": fix_id, "status": "running", "request": request.model_dump()}
    asyncio.create_task(_run_fix(fix_id, request))
    return {"fix_id": fix_id}


@router.get("/{fix_id}")
async def get_fix(fix_id: str):
    return _fix_jobs.get(fix_id, {})


@router.websocket("/ws/{fix_id}")
async def fix_ws(websocket: WebSocket, fix_id: str):
    await websocket.accept()
    q = ws_manager.subscribe(fix_id)
    try:
        while True:
            msg: Optional[WsMessage] = await q.get()
            if msg is None:
                break
            await websocket.send_text(msg.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unsubscribe(fix_id, q)
        await websocket.close()


async def _run_fix(fix_id: str, request: FixRequest) -> None:
    """Placeholder — Phase 3 will wire beets_fixer."""
    await ws_manager.broadcast(
        fix_id,
        WsMessage.make(WsEventType.fix_started, fix_id, operation=request.operation),
    )
    # TODO Phase 3: run beets_fixer.run_fix(fix_id, request)
    _fix_jobs[fix_id]["status"] = "complete"
    await ws_manager.broadcast(
        fix_id,
        WsMessage.make(WsEventType.fix_complete, fix_id, note="stub — Phase 3 pending"),
    )
    await ws_manager.close_job(fix_id)
