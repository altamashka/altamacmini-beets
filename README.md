# altamacmini-beets

A web-based music import and library management app for the altamacmini home server.

Replaces the beets CLI with a visual dashboard for:
- **Import**: browse downloads, run `beet import` with live progress, handle low-confidence matches interactively
- **Library Cleaner**: audit the existing music library for duplicates, missing artwork, bad metadata, and broken files — then fix them

## Stack

- **Backend**: FastAPI (Python 3.11) — direct beets Python API integration
- **Frontend**: React + Vite + TypeScript
- **Real-time**: WebSockets with per-job `asyncio.Queue`
- **Deployment**: single Docker container on altamacmini; FastAPI serves React static build

## Running locally (dev)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # Vite proxies /api → :8000
```

## Deployment (server)

```bash
# On altamacmini — after git pull
cd ~/docker/beets-manager
docker compose build
docker compose up -d
```

App will be available at `http://altamacmini:8765`.

## Volume mounts

| Purpose | Host path | Container path |
|---|---|---|
| Beets config | `~/.config/beets/config.yaml` | `/beets/config/config.yaml` (ro) |
| Beets library DB | `~/data/beets/library.db` | `/beets/db/library.db` (rw) |
| Music library | `~/data/media/music/` | `/data/media/music/` (rw) |
| Downloads | `~/data/downloads/completed/music/` | `/data/downloads/completed/music/` (rw) |
| Maintenance scripts | `~/scripts/` | `/scripts/` (ro) |

## Issue tracking

Uses [beads](https://github.com/steveyegge/beads) project-local issue tracker.

```bash
bd ready      # unblocked tasks
bd list       # all issues
bd show <id>  # full detail
```
