"""Downloads directory browser endpoints."""
from fastapi import APIRouter, HTTPException

from deps import run_in_executor
from services import downloads_browser

router = APIRouter(prefix="/api/downloads", tags=["downloads"])


@router.get("/browse")
async def browse(path: str = ""):
    try:
        return await run_in_executor(downloads_browser.list_downloads, path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
