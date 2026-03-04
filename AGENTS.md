# AGENTS.md — altamacmini-beets

Guidance for AI agents working in this repository. Read `CLAUDE.md` first for full context.

---

## Issue Tracking (Beads — project-local)

This project uses a **project-local** beads DB at `.beads/`. The JSONL file is committed to git so both Mac Claude and Server Claude see the same task list.

```bash
bd ready                                       # unblocked tasks
bd list                                        # all open issues
bd show <id>                                   # full detail + acceptance criteria
bd create "Title" --type task --priority 2     # create before every feature
bd comment <id> "note"                         # handoff notes between Claudes
bd sync --import                               # Server Claude: sync after git pull
~/scripts/complete_task.sh <id>               # Server Claude: close task + GitHub issue
```

---

## Agent Ground Rules

1. **Read before editing**: always read a file before modifying it.
2. **No passwordless sudo**: surface exact `sudo` commands to the user.
3. **Secrets**: never hardcode secrets. Use `.env` with `${VAR}` interpolation.
4. **No mass-adds**: use `git add <specific files>`, never `git add -A`.
5. **Single uvicorn worker**: beets Library is not safe across processes.
6. **Beets in executor**: all beets calls go through `run_in_executor` — never call beets from async code directly.
7. **Dry-run first**: always test beets operations with `--pretend` before mutating the live library.

---

## Agent Roles (for multi-agent task splits)

| Agent | Phases | Responsibility |
|---|---|---|
| `architect` | Phase 0 | Repo bootstrap, CLAUDE.md, beads init, docker-compose skeleton |
| `backend-dev` | Phases 1–3 | FastAPI routes, beets integration, services, models, WS bridge |
| `frontend-dev` | Phases 1–3 | Vite scaffold, React components, hooks, API client |
| `deployer` | Phase 4 | Dockerfile finalised, server build, end-to-end verification |

**Ghostty tmux pane layout (4-pane):**
```
┌──────────────────────┬──────────────────────┐
│  backend-dev         │  frontend-dev         │
│  (phases 1→2→3)      │  (phases 1→2→3)       │
├──────────────────────┼──────────────────────┤
│  deployer (phase 4)  │  architect (monitor)  │
└──────────────────────┴──────────────────────┘
```

---

## Key File Paths

```
backend/
  main.py              # FastAPI app entry point, /health, static mount
  config.py            # Path constants from env vars
  deps.py              # beets Library singleton (FastAPI Depends)
  requirements.txt
  routers/             # downloads, imports, library, audit, fixes, navidrome
  services/            # beets_library, beets_importer, beets_fixer, audit_runner, etc.
  models/              # Pydantic models: imports, library, websocket
  ws/                  # manager.py (asyncio.Queue registry), import_bridge.py

frontend/
  package.json
  vite.config.ts       # proxy /api → :8000 for local dev
  src/
    App.tsx            # Router + sidebar layout
    api/               # Axios client + typed API functions
    hooks/             # useWebSocket, useImportJob, useAuditState
    types/index.ts     # TypeScript mirrors of Pydantic models
    components/
      layout/          # Sidebar, Header, StatusBar
      shared/          # ProgressBar, ConfidenceBadge, MetadataDiff
      import/          # ImportPage + sub-components
      cleaner/         # CleanerPage + sub-components

Dockerfile             # Multi-stage: Node build → Python bundle
docker-compose.yml
.env.example
.beads/issues.jsonl    # committed — shared task list
```

---

## Docker Commands

```bash
# Build + deploy (Server Claude / Ben, in ~/docker/beets-manager/)
docker compose build
docker compose up -d
docker compose logs -f
docker compose down

# Validate compose config before applying
docker compose config
```

---

## WebSocket Events Quick Reference

| Event | Direction | Trigger |
|---|---|---|
| `import_started` | server → client | Import job begins |
| `album_begin` | server → client | Processing next album folder |
| `album_match` | server → client | MusicBrainz match found (includes diff) |
| `album_decision_needed` | server → client | Confidence < 90%, job pauses |
| `album_applying` | server → client | User decision received, applying |
| `album_complete` | server → client | Album imported successfully |
| `album_skipped` | server → client | Album skipped |
| `import_complete` | server → client | All albums done |
| `import_error` | server → client | Fatal error |
| `audit_started` | server → client | Audit scan begins |
| `audit_progress` | server → client | Issue found during scan |
| `audit_complete` | server → client | Scan done (counts by type) |
| `fix_started` | server → client | Fix operation begins |
| `fix_progress` | server → client | Fix step progress |
| `fix_complete` | server → client | Fix succeeded |
| `fix_error` | server → client | Fix failed |

---

## Beets Python API Usage Pattern

```python
# Always via executor — beets is synchronous
from beets.library import Library

async def get_albums(lib_path: str) -> list[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get_albums_sync, lib_path)

def _get_albums_sync(lib_path: str) -> list[dict]:
    with Library(lib_path) as lib:
        return [dict(a) for a in lib.albums()]
```

---

## Confidence Badge Colours

| Range | Colour | Meaning |
|---|---|---|
| ≥ 90% | Green | Auto-apply safe |
| 70–89% | Yellow | Review recommended |
| < 70% | Red | Manual decision required |

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
