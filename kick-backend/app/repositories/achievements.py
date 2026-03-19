"""Repository for achievement tracker."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_achievements(channel: str, game: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if game:
            row = await conn.execute(
                "SELECT * FROM achievements WHERE channel = %s AND game = %s ORDER BY created_at DESC",
                (channel, game),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM achievements WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_achievement(channel: str, game: str, title: str, description: str, icon: str) -> dict:
    ach_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO achievements (id, channel, game, title, description, icon, unlocked, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)""",
            (ach_id, channel, game, title, description, icon, now),
        )
        await conn.commit()
    return {
        "id": ach_id, "channel": channel, "game": game, "title": title,
        "description": description, "icon": icon, "unlocked": False, "created_at": now,
    }


async def unlock_achievement(channel: str, ach_id: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE achievements SET unlocked = TRUE, unlocked_at = %s WHERE id = %s AND channel = %s",
            (now, ach_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM achievements WHERE id = %s", (ach_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_achievement(channel: str, ach_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM achievements WHERE id = %s AND channel = %s",
            (ach_id, channel),
        )
        await conn.commit()
