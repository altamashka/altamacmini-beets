# CLAUDE.md — altamacmini-beets

Primary instruction set for Claude Code (and any AI agent) working on this repository.

**Two Claude instances work on this repo — know which one you are:**

---

## Instance Identity

### Mac-local Claude (`/Users/ben-home/Desktop/Projects/altamacmini-beets/`)

You are running on Ben's Mac and are the **development Claude**. Your role:
- Write and iterate on app code (backend + frontend)
- Push commits to `github.com/altamashka/altamacmini-beets` (token in git credential store)
- **Cannot** access the server filesystem, Docker daemon, beets, or the music library directly
- **Cannot** run `docker compose` against the server
- To deploy: commit + push, then tell Ben to `git pull && docker compose build && docker compose up -d` on the server
- Spawn agent teams in **Ghostty tmux panes** for live visibility of parallel work
- Always create a beads task with `bd create` before starting any feature (project-local `.beads/`)
- Mac beads binary: `/opt/homebrew/bin/beads` (v0.50.3)

### Server Claude (running on `altamacmini` at `~/docker/beets-manager/`)

You are running on the Ubuntu Server 24.04 machine and are the **operations Claude**. Your role:
- Direct access to the music library at `~/data/media/music/`
- Can run beets commands and `docker compose` lifecycle commands
- Can read/write `~/scripts/`, `~/data/`, `~/.config/beets/`
- **Cannot** passwordless sudo — surface exact `sudo` commands to Ben
- Server beads binary: `~/.local/bin/bd`
- Pulls app code from GitHub after Mac Claude pushes
- After `git pull`, run `bd sync --import` to sync beads tasks from JSONL into local Dolt DB

### Collaboration flow

```
Mac Claude                    GitHub                    Server Claude
   |                             |                            |
   |-- git push ---------------→ |                            |
   |                             |←-- git pull --------------|
   |                             |                            |-- docker compose build && up -d
   |                             |                            |-- verify /health endpoint
   |←-- Ben relays results ------|←-- Ben triggers ----------|
```

Leave handoff notes in beads (`bd comment <id> "..."`) and in git commit messages.

---

## Architecture

### Tech stack
- **Backend**: FastAPI + Python 3.11, **single uvicorn worker** (beets Library not safe across processes)
- **Frontend**: React + Vite + TypeScript
- **Real-time**: WebSockets with per-job `asyncio.Queue`
- **Beets**: Direct Python API (`from beets.library import Library`); all beets ops in `ThreadPoolExecutor`
- **Deployment**: Single Docker container; FastAPI serves React static build from `/app/frontend/dist/`

### Critical: threading boundary for beets

Beets is synchronous. All import/fix/audit operations run in `loop.run_in_executor(executor)`. Events bridge back to the asyncio event loop via:
```python
asyncio.run_coroutine_threadsafe(queue.put(event), loop)
```

Never call beets operations directly from async functions — always `await loop.run_in_executor(executor, fn, *args)`.

### Critical: low-confidence import handling

Beets fires `import_task_choice` for each album. The bridge intercepts it:
1. Confidence < 90%: puts `album_decision_needed` on the WS queue (job → `waiting_decision` state)
2. Blocks the beets thread on a `threading.Event`
3. `POST /api/import/jobs/{id}/decide` arrives → sets the Event with user's choice
4. Beets thread resumes with the chosen action

### Navidrome scan trigger

Via Subsonic API HTTP call (`GET /rest/startScan.view`), not `docker exec`. Requires `NAVIDROME_ADMIN_USER` + `NAVIDROME_ADMIN_PASS` env vars.

---

## Volume Mount Paths

| Purpose | Host path (server) | Container path |
|---|---|---|
| Beets config | `~/.config/beets/config.yaml` | `/beets/config/config.yaml` (ro) |
| Beets library DB | `~/data/beets/library.db` | `/beets/db/library.db` (rw) |
| Music library | `~/data/media/music/` | `/data/media/music/` (rw) |
| Downloads | `~/data/downloads/completed/music/` | `/data/downloads/completed/music/` (rw) |
| Maintenance scripts | `~/scripts/` | `/scripts/` (ro) |

Container env vars:
```
BEETS_CONFIG_PATH=/beets/config/config.yaml
BEETS_LIBRARY_PATH=/beets/db/library.db
MUSIC_ROOT=/data/media/music
DOWNLOADS_ROOT=/data/downloads/completed/music
```

---

## Dev Workflow

### Backend (local dev)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev    # Vite dev server on :5173, proxies /api → :8000
```

### Docker (server deployment)
```bash
# Server Claude or Ben, in ~/docker/beets-manager/
docker compose build
docker compose up -d
docker compose logs -f
```

### Build verification (server)
```bash
curl http://altamacmini:8765/health
# → {"status":"ok","library_db":"connected"}
```

---

## WebSocket Protocol

All messages: `{ event: string, job_id: str, timestamp: ISO8601, payload: {} }`

**Import events**: `import_started`, `album_begin`, `album_match`, `album_decision_needed`, `album_applying`, `album_complete`, `album_skipped`, `import_complete`, `import_error`

**Fix events**: `fix_started`, `fix_progress`, `fix_complete`, `fix_error`

**Audit events**: `audit_started`, `audit_progress`, `audit_complete`

Key `album_match` payload: `confidence`, `before/after {artist,album,year,genre,albumartist}`, `artwork {found,source,url}`, `tracks[]`

---

## Git Workflow

```bash
cd /Users/ben-home/Desktop/Projects/altamacmini-beets
git status
git add <specific files>   # never git add -A
git commit -m "type: description"
git push
```

Never commit `.env` (gitignored). Always verify `git diff --cached` before committing.

---

## Beads Workflow (project-local)

This repo uses a **project-local** beads DB at `.beads/`. Only `.beads/issues.jsonl` is committed to git.

```bash
# Mac Claude (in project root)
bd ready                              # unblocked tasks
bd list                               # all issues
bd show <id>                          # full detail
bd create "Title" --type task --priority 2   # always before starting a feature
bd comment <id> "handoff note"        # leave notes for Server Claude
~/scripts/complete_task.sh <id>       # close task + GitHub issue (server only)

# Server Claude — after git pull
bd sync --import                      # sync JSONL → local Dolt DB
```

**Mac Claude**: use `/opt/homebrew/bin/beads` binary (or `bd` if on PATH).
**Server Claude**: use `~/.local/bin/bd`.

---

## Sudo Operations

Server has **no passwordless sudo**. Surface exact commands to Ben:
- Never attempt sudo directly
- Write commands to a `.txt` file at `~/` for copy-paste

---

## Testing Beets Operations

Always run beets in dry-run / read-only mode before any write operations on the live library:
```bash
beet import --pretend ~/data/downloads/completed/music/<folder>
beet list -a <query>   # read-only
```

---

## Verification Checklist (post-deploy)

1. `GET http://altamacmini:8765/health` → `{"status":"ok","library_db":"connected"}`
2. Open `http://altamacmini:8765` → Sidebar shows Import + Library Cleaner
3. Import page: downloads folder tree loads
4. Select folder → Start Import → WS stream shows album cards with confidence scores
5. Cleaner page: Run Audit Scan → issues checklist appears
6. Fix a missing artwork issue → WS progress → checkbox ticks green
7. `docker logs beets-manager` — no errors
8. `bd list` → all tasks with correct statuses
