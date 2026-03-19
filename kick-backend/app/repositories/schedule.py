"""Repository for stream schedule entries."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_entries(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_schedules WHERE channel = %s ORDER BY day_of_week, start_time",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_entry(
    channel: str, day_of_week: int, start_time: str, end_time: str,
    title: str, game: str, recurring: bool, enabled: bool,
) -> dict:
    entry_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_schedules
               (id, channel, day_of_week, start_time, end_time, title, game, recurring, enabled, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (entry_id, channel, day_of_week, start_time, end_time, title, game, recurring, enabled, now),
        )
        await conn.commit()
    return {
        "id": entry_id, "channel": channel, "day_of_week": day_of_week,
        "start_time": start_time, "end_time": end_time, "title": title,
        "game": game, "recurring": recurring, "enabled": enabled, "created_at": now,
    }


async def update_entry(channel: str, entry_id: str, **kwargs: object) -> Optional[dict]:
    if not kwargs:
        return None
    set_parts = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            set_parts.append(f"{key} = %s")
            values.append(value)
    if not set_parts:
        return None
    values.extend([entry_id, channel])
    async with get_conn() as conn:
        row = await conn.execute(
            f"UPDATE stream_schedules SET {', '.join(set_parts)} WHERE id = %s AND channel = %s RETURNING *",
            tuple(values),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def delete_entry(channel: str, entry_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM stream_schedules WHERE id = %s AND channel = %s",
            (entry_id, channel),
        )
        await conn.commit()


async def get_public_schedule(channel: str) -> list[dict]:
    """Get schedule entries for a public profile (only enabled entries)."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT day_of_week, start_time, end_time, title, game
               FROM stream_schedules WHERE channel = %s AND enabled = TRUE
               ORDER BY day_of_week, start_time""",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]
