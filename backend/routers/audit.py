"""Audit scan endpoints + WebSocket stream.

Phase 3 implementation — stubs here, full logic in services/audit_runner.py.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.websocket import WsEventType, WsMessage
from ws.manager import ws_manager

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
    """Placeholder — Phase 3 will wire audit_runner."""
    await ws_manager.broadcast(scan_id, WsMessage.make(WsEventType.audit_started, scan_id))
    # TODO Phase 3: run audit_runner.run_audit(scan_id)
    _scans[scan_id]["status"] = "complete"
    await ws_manager.broadcast(
        scan_id,
        WsMessage.make(WsEventType.audit_complete, scan_id, note="stub — Phase 3 pending"),
    )
    await ws_manager.close_job(scan_id)
