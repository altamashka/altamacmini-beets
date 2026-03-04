"""FastAPI application entry point.

Single uvicorn worker — beets Library is not safe across processes.
Serves the React frontend static build from /app/frontend/dist/ in production.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import audit, downloads, fixes, imports, library, navidrome
from services.beets_library import is_library_connected


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the beets library connection on startup
    try:
        is_library_connected()
    except Exception as e:
        print(f"[startup] beets library check failed: {e}")
    yield


app = FastAPI(title="altamacmini-beets", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(library.router)
app.include_router(downloads.router)
app.include_router(imports.router)
app.include_router(audit.router)
app.include_router(fixes.router)
app.include_router(navidrome.router)


@app.get("/health")
async def health():
    connected = is_library_connected()
    return {
        "status": "ok",
        "library_db": "connected" if connected else "disconnected",
    }


# Serve React frontend in production (when dist/ exists)
_dist = "/app/frontend/dist"
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=f"{_dist}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(f"{_dist}/index.html")
