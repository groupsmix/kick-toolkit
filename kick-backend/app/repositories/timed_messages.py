"""Repository for timed messages."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_messages(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM timed_messages WHERE channel = %s ORDER BY created_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_message(channel: str, message: str, interval_minutes: int, enabled: bool) -> dict:
    msg_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO timed_messages (id, channel, message, interval_minutes, enabled, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (msg_id, channel, message, interval_minutes, enabled, now),
        )
        await conn.commit()
    return {
        "id": msg_id, "channel": channel, "message": message,
        "interval_minutes": interval_minutes, "enabled": enabled, "created_at": now,
    }


async def update_message(channel: str, msg_id: str, **kwargs) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM timed_messages WHERE id = %s AND channel = %s",
            (msg_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None

        data = dict(existing)
        data.update(kwargs)
        await conn.execute(
            """UPDATE timed_messages SET message = %s, interval_minutes = %s, enabled = %s
               WHERE id = %s AND channel = %s""",
            (data["message"], data["interval_minutes"], data["enabled"], msg_id, channel),
        )
        await conn.commit()
    return data


async def delete_message(channel: str, msg_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM timed_messages WHERE id = %s AND channel = %s",
            (msg_id, channel),
        )
        await conn.commit()
