"""Repository for Stream Intelligence Dashboard data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


async def create_session(
    channel: str,
    duration_minutes: int = 0,
    peak_viewers: int = 0,
    avg_viewers: float = 0.0,
    chat_messages: int = 0,
    new_followers: int = 0,
    new_subscribers: int = 0,
    game: str = "",
    title: str = "",
) -> dict:
    sid = _generate_id()
    now = _now_iso()
    # Calculate stream score (weighted formula)
    viewer_score = min(100, (avg_viewers / 5) + (peak_viewers / 10))
    chat_score = min(100, (chat_messages / (max(duration_minutes, 1))) * 5)
    growth_score = min(100, (new_followers * 2) + (new_subscribers * 5))
    stream_score = round(viewer_score * 0.35 + chat_score * 0.30 + growth_score * 0.35, 1)

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_intel_sessions
               (id, channel, started_at, ended_at, duration_minutes, peak_viewers, avg_viewers,
                chat_messages, new_followers, new_subscribers, stream_score, game, title)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (sid, channel, now, None, duration_minutes, peak_viewers, avg_viewers,
             chat_messages, new_followers, new_subscribers, stream_score, game, title),
        )
        await conn.commit()
    return {
        "id": sid, "channel": channel, "started_at": now, "ended_at": None,
        "duration_minutes": duration_minutes, "peak_viewers": peak_viewers,
        "avg_viewers": avg_viewers, "chat_messages": chat_messages,
        "new_followers": new_followers, "new_subscribers": new_subscribers,
        "stream_score": stream_score, "game": game, "title": title,
    }


async def get_sessions(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM stream_intel_sessions
               WHERE channel = %s ORDER BY started_at DESC LIMIT %s""",
            (channel, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_stream_score(channel: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM stream_scores WHERE channel = %s", (channel,),
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def upsert_stream_score(
    channel: str,
    overall_score: float,
    viewer_score: float,
    chat_score: float,
    growth_score: float,
    consistency_score: float,
    trend: str,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_scores
               (channel, overall_score, viewer_score, chat_score, growth_score,
                consistency_score, trend, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (channel) DO UPDATE SET
                 overall_score = EXCLUDED.overall_score,
                 viewer_score = EXCLUDED.viewer_score,
                 chat_score = EXCLUDED.chat_score,
                 growth_score = EXCLUDED.growth_score,
                 consistency_score = EXCLUDED.consistency_score,
                 trend = EXCLUDED.trend,
                 updated_at = EXCLUDED.updated_at""",
            (channel, overall_score, viewer_score, chat_score,
             growth_score, consistency_score, trend, now),
        )
        await conn.commit()
    return {
        "channel": channel, "overall_score": overall_score,
        "viewer_score": viewer_score, "chat_score": chat_score,
        "growth_score": growth_score, "consistency_score": consistency_score,
        "trend": trend, "updated_at": now,
    }


async def get_best_times(channel: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT day_of_week, hour, competition_score, recommended_score,
                      avg_category_viewers, active_streamers
               FROM best_time_slots WHERE channel = %s
               ORDER BY recommended_score DESC""",
            (channel,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_overview(channel: str) -> dict:
    score = await get_stream_score(channel)
    sessions = await get_sessions(channel, limit=10)
    best_times = await get_best_times(channel)

    if not score:
        score = {
            "channel": channel, "overall_score": 0, "viewer_score": 0,
            "chat_score": 0, "growth_score": 0, "consistency_score": 0, "trend": "stable",
        }

    # Weekly summary
    weekly = {
        "total_streams": len([s for s in sessions if s.get("stream_score", 0) > 0]),
        "avg_score": round(sum(s.get("stream_score", 0) for s in sessions if s.get("stream_score", 0) > 0) /
                          max(1, len([s for s in sessions if s.get("stream_score", 0) > 0])), 1),
        "total_viewers": sum(s.get("peak_viewers", 0) for s in sessions),
        "total_followers": sum(s.get("new_followers", 0) for s in sessions),
        "total_messages": sum(s.get("chat_messages", 0) for s in sessions),
    }

    # Game recommendations (based on session data)
    game_stats: dict[str, dict] = {}
    for s in sessions:
        g = s.get("game", "")
        if not g:
            continue
        if g not in game_stats:
            game_stats[g] = {"total_score": 0, "count": 0, "total_viewers": 0}
        game_stats[g]["total_score"] += s.get("stream_score", 0)
        game_stats[g]["count"] += 1
        game_stats[g]["total_viewers"] += s.get("avg_viewers", 0)

    game_recs = []
    for game, stats in sorted(game_stats.items(), key=lambda x: x[1]["total_score"] / max(1, x[1]["count"]), reverse=True):
        avg_score = stats["total_score"] / max(1, stats["count"])
        game_recs.append({
            "game": game,
            "growth_potential": round(avg_score, 1),
            "competition_level": "low" if avg_score > 80 else "medium" if avg_score > 60 else "high",
            "avg_viewers_in_category": int(stats["total_viewers"] / max(1, stats["count"])),
            "trending": avg_score > 80,
            "reason": f"Avg score {avg_score:.0f}/100 across {stats['count']} streams",
        })

    return {
        "channel": channel,
        "stream_score": score,
        "recent_sessions": sessions,
        "best_times": best_times[:5],
        "game_recommendations": game_recs,
        "weekly_summary": weekly,
    }
