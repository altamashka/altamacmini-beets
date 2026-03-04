"""Trigger a Navidrome library scan via the Subsonic API."""
from __future__ import annotations

import httpx

from config import NAVIDROME_ADMIN_PASS, NAVIDROME_ADMIN_USER, NAVIDROME_URL


async def trigger_scan() -> dict:
    """POST to Navidrome Subsonic startScan endpoint."""
    params = {
        "u": NAVIDROME_ADMIN_USER,
        "p": NAVIDROME_ADMIN_PASS,
        "v": "1.16.1",
        "c": "beets-manager",
        "f": "json",
    }
    url = f"{NAVIDROME_URL}/rest/startScan.view"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("subsonic-response", {}).get("status", "unknown")
        return {"status": status, "raw": data}
