"""Import pipeline endpoints + WebSocket stream.

Phase 2 implementation — stubs here, full logic in services/beets_importer.py.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from deps import get_executor, run_in_executor
from models.imports import DecisionRequest, ImportJob, ImportJobStatus, ImportRequest
from models.websocket import WsEventType, WsMessage
from services import downloads_browser
from ws.manager import ws_manager

router = APIRouter(prefix="/api/import", tags=["imports"])

# In-memory job registry — sufficient for single-worker deployment
_jobs: dict[str, ImportJob] = {}
_bridges: dict[str, object] = {}  # job_id → ImportBridge (filled in Phase 2)


@router.post("/jobs", response_model=ImportJob, status_code=201)
async def create_import_job(request: ImportRequest):
    """Validate paths and enqueue an import job."""
    try:
        abs_paths = await run_in_executor(
            downloads_browser.resolve_import_paths, request.paths
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    job_id = str(uuid.uuid4())
    job = ImportJob(id=job_id, status=ImportJobStatus.pending, paths=abs_paths)
    _jobs[job_id] = job

    # Kick off in background
    asyncio.create_task(_run_import(job_id))
    return job


@router.get("/jobs/{job_id}", response_model=ImportJob)
async def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/decide")
async def decide(job_id: str, body: DecisionRequest):
    bridge = _bridges.get(job_id)
    if not bridge:
        raise HTTPException(status_code=404, detail="No pending decision for this job")
    bridge.resolve_decision(body.decision.value)
    return {"ok": True}


@router.websocket("/ws/{job_id}")
async def import_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    q = ws_manager.subscribe(job_id)
    try:
        while True:
            msg: Optional[WsMessage] = await q.get()
            if msg is None:
                break
            await websocket.send_text(msg.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unsubscribe(job_id, q)
        await websocket.close()


async def _run_import(job_id: str) -> None:
    """Placeholder: full implementation wired up in Phase 2."""
    job = _jobs[job_id]
    job.status = ImportJobStatus.running
    loop = asyncio.get_event_loop()

    msg = WsMessage.make(WsEventType.import_started, job_id, paths=job.paths)
    await ws_manager.broadcast(job_id, msg)

    # TODO Phase 2: wire beets_importer.run_import(job, bridge)
    job.status = ImportJobStatus.complete
    done_msg = WsMessage.make(WsEventType.import_complete, job_id, note="stub — Phase 2 pending")
    await ws_manager.broadcast(job_id, done_msg)
    await ws_manager.close_job(job_id)
