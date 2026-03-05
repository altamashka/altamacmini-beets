"""Audit scan endpoints + WebSocket stream."""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from deps import get_executor
from models.websocket import WsEventType, WsMessage
from services import audit_runner
from ws.manager import ws_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])

_scans: dict[str, dict] = {}


@router.post("/scans", status_code=201)
async def start_scan():
    scan_id = str(uuid.uuid4())
    _scans[scan_id] = {"id": scan_id, "status": "running", "issues": []}
    asyncio.create_task(_run_audit(scan_id))
    return {"scan_id": scan_id}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
    return _scans.get(scan_id, {})


@router.websocket("/ws/{scan_id}")
async def audit_ws(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    q = ws_manager.subscribe(scan_id)
    try:
        while True:
            msg: Optional[WsMessage] = await q.get()
            if msg is None:
                break
            await websocket.send_text(msg.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unsubscribe(scan_id, q)
        await websocket.close()


async def _run_audit(scan_id: str) -> None:
    loop = asyncio.get_event_loop()
    await ws_manager.broadcast(scan_id, WsMessage.make(WsEventType.audit_started, scan_id))
    try:
        issues = await loop.run_in_executor(get_executor(), audit_runner.run_audit, scan_id, loop)
        _scans[scan_id]["issues"] = [i.model_dump() for i in issues]
        _scans[scan_id]["status"] = "complete"
        counts: dict = {}
        for issue in issues:
            counts[issue.type] = counts.get(issue.type, 0) + 1
        await ws_manager.broadcast(
            scan_id,
            WsMessage.make(WsEventType.audit_complete, scan_id, counts=counts, total=len(issues)),
        )
    except Exception as e:
        _scans[scan_id]["status"] = "error"
        _scans[scan_id]["error"] = str(e)
        log.exception("Audit scan failed: %s", scan_id)
    finally:
        await ws_manager.close_job(scan_id)
