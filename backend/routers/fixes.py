"""Fix operation endpoints + WebSocket stream."""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from deps import get_executor
from models.library import FixRequest, FixResult
from models.websocket import WsEventType, WsMessage
from services import beets_fixer
from ws.manager import ws_manager

log = logging.getLogger(__name__)

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
    loop = asyncio.get_event_loop()
    await ws_manager.broadcast(fix_id, WsMessage.make(WsEventType.fix_started, fix_id, operation=request.operation))
    try:
        album_id = int(request.params.get("album_id", 0))
        if not album_id:
            raise ValueError("params.album_id is required")

        op_map = {
            "fetchart": beets_fixer.fetchart,
            "fix_albumartist": beets_fixer.fix_albumartist,
            "fix_tracknums": beets_fixer.fix_tracknums,
            "unify_mbids": beets_fixer.unify_mbids,
            "delete_album": beets_fixer.delete_album,
        }
        fn = op_map.get(request.operation)
        if fn is None:
            raise ValueError(f"Unknown operation: {request.operation}")

        fix_result = await loop.run_in_executor(get_executor(), fn, album_id)

        results = [
            FixResult(issue_id=iid, success=fix_result.get("ok", False), message=str(fix_result))
            for iid in request.issue_ids
        ]
        _fix_jobs[fix_id]["status"] = "complete"
        _fix_jobs[fix_id]["results"] = [r.model_dump() for r in results]
        await ws_manager.broadcast(
            fix_id,
            WsMessage.make(WsEventType.fix_complete, fix_id, results=[r.model_dump() for r in results]),
        )
    except Exception as e:
        _fix_jobs[fix_id]["status"] = "error"
        log.exception("Fix job failed: %s", fix_id)
        await ws_manager.broadcast(fix_id, WsMessage.make(WsEventType.fix_error, fix_id, error=str(e)))
    finally:
        await ws_manager.close_job(fix_id)
