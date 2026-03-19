"""Repository for rank tracker."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_ranks(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM rank_trackers WHERE channel = %s ORDER BY updated_at DESC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_rank(channel: str, game: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM rank_trackers WHERE channel = %s AND game = %s",
            (channel, game),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_rank(channel: str, game: str, current_rank: str,
                      rank_points: int, peak_rank: Optional[str] = None) -> dict:
    now = _now_iso()
    existing = await get_rank(channel, game)
    if existing:
        p = peak_rank if peak_rank else existing["peak_rank"]
        async with get_conn() as conn:
            await conn.execute(
                """UPDATE rank_trackers SET current_rank = %s, rank_points = %s, peak_rank = %s, updated_at = %s
                   WHERE channel = %s AND game = %s""",
                (current_rank, rank_points, p, now, channel, game),
            )
            await conn.commit()
        return {
            "id": existing["id"], "channel": channel, "game": game,
            "current_rank": current_rank, "peak_rank": p,
            "rank_points": rank_points, "updated_at": now,
        }
    else:
        rank_id = _generate_id()
        p = peak_rank if peak_rank else current_rank
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO rank_trackers (id, channel, game, current_rank, peak_rank, rank_points, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (rank_id, channel, game, current_rank, p, rank_points, now),
            )
            await conn.commit()
        return {
            "id": rank_id, "channel": channel, "game": game,
            "current_rank": current_rank, "peak_rank": p,
            "rank_points": rank_points, "updated_at": now,
        }


async def delete_rank(channel: str, game: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM rank_trackers WHERE channel = %s AND game = %s",
            (channel, game),
        )
        await conn.commit()
