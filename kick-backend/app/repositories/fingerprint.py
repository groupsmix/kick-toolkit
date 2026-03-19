"""Repository for fingerprint data access."""

from typing import Optional

from app.services.db import get_conn


async def get_fingerprint(username: str, channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM user_fingerprints WHERE username = %s AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def list_fingerprints(channel: str, limit: int = 100) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM user_fingerprints WHERE channel = %s ORDER BY last_seen DESC LIMIT %s",
            (channel, limit),
        )
        return [dict(r) for r in await row.fetchall()]
