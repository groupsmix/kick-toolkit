"""Repository for stream intelligence dashboard — sessions, scores, growth metrics."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Stream Intel Sessions
# ---------------------------------------------------------------------------

async def create_session(channel: str, started_at: str, game: str = "") -> dict:
    session_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_intel_sessions
               (id, channel, started_at, game, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (session_id, channel, started_at, game, now),
        )
        await conn.commit()
    return {
        "id": session_id, "channel": channel, "started_at": started_at,
        "ended_at": None, "duration_minutes": 0, "avg_viewers": 0,
        "peak_viewers": 0, "new_followers": 0, "messages_count": 0,
        "unique_chatters": 0, "game": game, "stream_score": 0, "created_at": now,
    }


async def update_session(session_id: str, **kwargs: object) -> Optional[dict]:
    if not kwargs:
        return None
    set_parts = []
    values: list[object] = []
    for key, val in kwargs.items():
        set_parts.append(f"{key} = %s")
        values.append(val)
    values.append(session_id)
    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE stream_intel_sessions SET {', '.join(set_parts)} WHERE id = %s",
            tuple(values),
        )
        await conn.commit()
        row = await conn.execute(
            "SELECT * FROM stream_intel_sessions WHERE id = %s", (session_id,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def get_session(session_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_intel_sessions WHERE id = %s", (session_id,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def list_sessions(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM stream_intel_sessions WHERE channel = %s
               ORDER BY started_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def delete_session(session_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM stream_intel_sessions WHERE id = %s", (session_id,)
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Growth Metrics (computed from stored sessions)
# ---------------------------------------------------------------------------

async def get_growth_metrics(channel: str, days: int = 30) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT
                 COUNT(*) AS stream_count,
                 COALESCE(AVG(avg_viewers), 0) AS avg_viewers,
                 COALESCE(MAX(peak_viewers), 0) AS peak_viewers,
                 COALESCE(SUM(new_followers), 0) AS total_followers,
                 COALESCE(SUM(messages_count), 0) AS total_messages,
                 COALESCE(AVG(stream_score), 0) AS avg_stream_score
               FROM stream_intel_sessions
               WHERE channel = %s
                 AND created_at >= NOW() - INTERVAL '%s days'""",
            (channel, days),
        )
        result = await row.fetchone()

    if not result or result["stream_count"] == 0:
        return {
            "channel": channel,
            "period": f"{days}d",
            "viewer_trend": 0.0,
            "follower_trend": 0.0,
            "chat_trend": 0.0,
            "stream_count": 0,
            "avg_stream_score": 0,
        }

    return {
        "channel": channel,
        "period": f"{days}d",
        "viewer_trend": 0.0,
        "follower_trend": 0.0,
        "chat_trend": 0.0,
        "stream_count": int(result["stream_count"]),
        "avg_stream_score": int(result["avg_stream_score"]),
    }


async def get_best_time_slots(channel: str) -> list[dict]:
    """Analyze past sessions to find best streaming times."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM stream_intel_sessions
               WHERE channel = %s AND stream_score > 0
               ORDER BY stream_score DESC LIMIT 50""",
            (channel,),
        )
        results = await row.fetchall()

    # Aggregate by day/hour from started_at
    slot_data: dict[tuple[int, int], list[int]] = {}
    for r in results:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(r["started_at"].replace("Z", "+00:00"))
            key = (dt.weekday(), dt.hour)
            slot_data.setdefault(key, []).append(r["avg_viewers"])
        except (ValueError, KeyError):
            continue

    slots = []
    for (day, hour), viewers in sorted(slot_data.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        avg = sum(viewers) / len(viewers)
        slots.append({
            "day_of_week": day,
            "hour": hour,
            "score": round(avg, 1),
            "avg_viewers": round(avg, 1),
            "competition_level": "low" if avg > 100 else "medium" if avg > 30 else "high",
        })
    return slots[:10]


async def get_game_performance(channel: str) -> list[dict]:
    """Analyze which games perform best for the streamer."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT game,
                      COUNT(*) AS streams,
                      AVG(avg_viewers) AS avg_viewers,
                      AVG(stream_score) AS avg_score,
                      SUM(new_followers) AS total_followers
               FROM stream_intel_sessions
               WHERE channel = %s AND game != ''
               GROUP BY game ORDER BY avg_score DESC""",
            (channel,),
        )
        results = await row.fetchall()
    return [
        {
            "game": r["game"],
            "streams": int(r["streams"]),
            "avg_viewers": round(float(r["avg_viewers"]), 1),
            "avg_score": round(float(r["avg_score"]), 1),
            "total_followers": int(r["total_followers"]),
        }
        for r in results
    ]


# ---------------------------------------------------------------------------
# Weekly Reports
# ---------------------------------------------------------------------------

async def get_weekly_report(channel: str, week_start: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM weekly_reports WHERE channel = %s AND week_start = %s",
            (channel, week_start),
        )
        result = await row.fetchone()
    if result:
        return dict(result)
    return None


async def upsert_weekly_report(
    channel: str, week_start: str, week_end: str,
    total_streams: int, total_hours: float, avg_viewers: int,
    peak_viewers: int, total_followers_gained: int, total_messages: int,
    avg_stream_score: int, best_stream_id: Optional[str], summary: str,
) -> dict:
    report_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO weekly_reports
               (id, channel, week_start, week_end, total_streams, total_hours,
                avg_viewers, peak_viewers, total_followers_gained, total_messages,
                avg_stream_score, best_stream_id, summary, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel, week_start) DO UPDATE SET
                   week_end = EXCLUDED.week_end, total_streams = EXCLUDED.total_streams,
                   total_hours = EXCLUDED.total_hours, avg_viewers = EXCLUDED.avg_viewers,
                   peak_viewers = EXCLUDED.peak_viewers,
                   total_followers_gained = EXCLUDED.total_followers_gained,
                   total_messages = EXCLUDED.total_messages,
                   avg_stream_score = EXCLUDED.avg_stream_score,
                   best_stream_id = EXCLUDED.best_stream_id,
                   summary = EXCLUDED.summary""",
            (report_id, channel, week_start, week_end, total_streams, total_hours,
             avg_viewers, peak_viewers, total_followers_gained, total_messages,
             avg_stream_score, best_stream_id, summary, now),
        )
        await conn.commit()
    return {
        "id": report_id, "channel": channel, "week_start": week_start,
        "week_end": week_end, "total_streams": total_streams,
        "total_hours": total_hours, "avg_viewers": avg_viewers,
        "peak_viewers": peak_viewers, "total_followers_gained": total_followers_gained,
        "total_messages": total_messages, "avg_stream_score": avg_stream_score,
        "best_stream_id": best_stream_id, "summary": summary, "created_at": now,
    }


async def list_weekly_reports(channel: str, limit: int = 12) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM weekly_reports WHERE channel = %s
               ORDER BY week_start DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]
