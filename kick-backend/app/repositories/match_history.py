"""Repository for match history tracker."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def list_matches(channel: str, game: Optional[str] = None, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        if game:
            row = await conn.execute(
                "SELECT * FROM match_records WHERE channel = %s AND game = %s ORDER BY played_at DESC LIMIT %s",
                (channel, game, limit),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM match_records WHERE channel = %s ORDER BY played_at DESC LIMIT %s",
                (channel, limit),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_match(channel: str, game: str, opponent: str, result: str, score: str, notes: str) -> dict:
    match_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO match_records (id, channel, game, opponent, result, score, notes, played_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (match_id, channel, game, opponent, result, score, notes, now),
        )
        await conn.commit()
    return {
        "id": match_id, "channel": channel, "game": game, "opponent": opponent,
        "result": result, "score": score, "notes": notes, "played_at": now,
    }


async def delete_match(channel: str, match_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM match_records WHERE id = %s AND channel = %s",
            (match_id, channel),
        )
        await conn.commit()


async def get_stats(channel: str, game: Optional[str] = None) -> dict:
    async with get_conn() as conn:
        if game:
            row = await conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                          SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) as draws
                   FROM match_records WHERE channel = %s AND game = %s""",
                (channel, game),
            )
        else:
            row = await conn.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                          SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END) as draws
                   FROM match_records WHERE channel = %s""",
                (channel,),
            )
        result = await row.fetchone()

    total = result["total"] if result else 0
    wins = result["wins"] or 0 if result else 0
    losses = result["losses"] or 0 if result else 0
    draws = result["draws"] or 0 if result else 0
    win_rate = (wins / total * 100) if total > 0 else 0.0

    # Get streak
    matches = await list_matches(channel, game, limit=20)
    streak = 0
    streak_type = ""
    for m in matches:
        if not streak_type:
            streak_type = m["result"]
            streak = 1
        elif m["result"] == streak_type:
            streak += 1
        else:
            break

    # By-game breakdown
    by_game: list[dict] = []
    if not game:
        async with get_conn() as conn:
            row = await conn.execute(
                """SELECT game, COUNT(*) as total,
                          SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                          SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses
                   FROM match_records WHERE channel = %s GROUP BY game""",
                (channel,),
            )
            results = await row.fetchall()
        by_game = [dict(r) for r in results]

    return {
        "channel": channel, "total_matches": total, "wins": wins, "losses": losses,
        "draws": draws, "win_rate": round(win_rate, 1),
        "current_streak": streak, "streak_type": streak_type, "by_game": by_game,
    }
