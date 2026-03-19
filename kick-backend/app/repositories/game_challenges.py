"""Repository for game challenge system."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_challenges(channel: str, status: Optional[str] = None) -> list[dict]:
    async with get_conn() as conn:
        if status:
            row = await conn.execute(
                "SELECT * FROM game_challenges WHERE channel = %s AND status = %s ORDER BY created_at DESC",
                (channel, status),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM game_challenges WHERE channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_challenge(channel: str, title: str, description: str,
                           reward_points: int, creator_username: str) -> dict:
    ch_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO game_challenges (id, channel, creator_username, title, description, reward_points, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)""",
            (ch_id, channel, creator_username, title, description, reward_points, now),
        )
        await conn.commit()
    return {
        "id": ch_id, "channel": channel, "creator_username": creator_username,
        "title": title, "description": description, "reward_points": reward_points,
        "status": "pending", "created_at": now,
    }


async def update_status(channel: str, challenge_id: str, status: str) -> Optional[dict]:
    now = _now_iso()
    async with get_conn() as conn:
        completed_at = now if status in ("completed", "failed") else None
        await conn.execute(
            "UPDATE game_challenges SET status = %s, completed_at = %s WHERE id = %s AND channel = %s",
            (status, completed_at, challenge_id, channel),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM game_challenges WHERE id = %s", (challenge_id,))
        result = await row.fetchone()
    return dict(result) if result else None


async def delete_challenge(channel: str, challenge_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM game_challenges WHERE id = %s AND channel = %s",
            (challenge_id, channel),
        )
        await conn.commit()
