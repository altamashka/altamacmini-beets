"""Navidrome scan trigger endpoint."""
from fastapi import APIRouter, HTTPException

from services.navidrome_trigger import trigger_scan

router = APIRouter(prefix="/api/navidrome", tags=["navidrome"])


@router.post("/scan")
async def start_scan():
    try:
        return await trigger_scan()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Navidrome scan failed: {e}")
