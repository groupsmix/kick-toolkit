"""Repository for behavior profile data access."""

from typing import Optional

from app.services.db import get_conn


async def get_profile(username: str, channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM behavior_profiles WHERE username = %s AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def list_profiles(channel: str, limit: int = 100) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM behavior_profiles WHERE channel = %s ORDER BY updated_at DESC LIMIT %s",
            (channel, limit),
        )
        return [dict(r) for r in await row.fetchall()]


async def delete_profile(username: str, channel: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM behavior_profiles WHERE username = %s AND channel = %s",
            (username, channel),
        )
        await conn.commit()
