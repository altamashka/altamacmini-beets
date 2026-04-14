"""Import pipeline endpoints + WebSocket stream."""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from deps import get_executor, run_in_executor
from models.imports import DecisionRequest, ImportJob, ImportJobStatus, ImportRequest
from models.websocket import WsEventType, WsMessage
from services import downloads_browser
from services.beets_importer import run_import
from services.downloads_browser import count_audio_files
from ws.import_bridge import ImportBridge
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
    job = _jobs[job_id]
    job.status = ImportJobStatus.running
    loop = asyncio.get_event_loop()

    bridge = ImportBridge(job_id, loop)
    _bridges[job_id] = bridge

    # Pre-scan: filter out folders with no audio so beets doesn't silently drop them.
    importable: list[str] = []
    pre_skipped = 0
    for path in job.paths:
        if await run_in_executor(count_audio_files, path) > 0:
            importable.append(path)
        else:
            pre_skipped += 1
            bridge.on_album_begin(path)
            bridge.on_album_skipped("no audio files found in folder")

    job.albums_total = len(job.paths)

    if not importable:
        job.albums_skipped = pre_skipped
        job.status = ImportJobStatus.complete
        bridge.on_import_complete({
            "albums_imported": 0,
            "albums_skipped": pre_skipped,
            "albums_error": 0,
        })
        _bridges.pop(job_id, None)
        await ws_manager.close_job(job_id)
        return

    try:
        stats = await loop.run_in_executor(
            get_executor(),
            run_import,
            job_id,
            importable,
            bridge,
        )
        job.albums_done = stats.get("albums_imported", 0)
        job.albums_skipped = stats.get("albums_skipped", 0) + pre_skipped
        if stats.get("albums_error", 0) > 0:
            job.status = ImportJobStatus.error
            job.error = "Beets import failed — check container logs"
        else:
            job.status = ImportJobStatus.complete
    except Exception as e:
        job.status = ImportJobStatus.error
        job.error = str(e)
    finally:
        _bridges.pop(job_id, None)
        await ws_manager.close_job(job_id)
