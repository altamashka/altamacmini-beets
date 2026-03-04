"""Read-only library browsing endpoints."""
from fastapi import APIRouter, HTTPException

from deps import run_in_executor
from models.library import AlbumInfo
from services import beets_library

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/albums", response_model=list[AlbumInfo])
async def list_albums(q: str = ""):
    return await run_in_executor(beets_library.list_albums, q)


@router.get("/albums/{album_id}", response_model=AlbumInfo)
async def get_album(album_id: int):
    album = await run_in_executor(beets_library.get_album, album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return album


@router.get("/stats")
async def library_stats():
    return await run_in_executor(beets_library.library_stats)
