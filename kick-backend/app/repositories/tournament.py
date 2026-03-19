"""Repository for tournament data access."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_tournaments(channel: str = "") -> list[dict]:
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM tournaments WHERE channel = %s ORDER BY created_at DESC", (channel,)
            )
        else:
            row = await conn.execute("SELECT * FROM tournaments ORDER BY created_at DESC")
        return [dict(t) for t in await row.fetchall()]


async def create(name: str, channel: str, game: str, max_participants: int, fmt: str, keyword: str) -> dict:
    t_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO tournaments (id, name, channel, game, max_participants, format, keyword,
               status, participants, matches, current_round, winner, created_at, started_at, ended_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (t_id, name, channel, game, max_participants, fmt,
             keyword, "registration", "[]", "[]", 0, None, now, None, None),
        )
        await conn.commit()
    return {
        "id": t_id, "name": name, "channel": channel, "game": game,
        "max_participants": max_participants, "format": fmt, "keyword": keyword,
        "status": "registration", "participants": [], "matches": [],
        "current_round": 0, "winner": None, "created_at": now,
        "started_at": None, "ended_at": None,
    }


async def get_by_id(tournament_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()
    return dict(t) if t else None


async def update_tournament(tournament_id: str, **fields: object) -> Optional[dict]:
    """Update tournament fields and return the updated record."""
    async with get_conn() as conn:
        set_clauses = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [tournament_id]
        await conn.execute(
            f"UPDATE tournaments SET {set_clauses} WHERE id = %s",
            values,
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        return dict(await row.fetchone())


async def delete(tournament_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM tournaments WHERE id = %s", (tournament_id,))
        await conn.commit()
