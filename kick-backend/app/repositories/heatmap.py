"""Repository for Viewer Heatmap data access."""

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Viewer Sessions
# ---------------------------------------------------------------------------

async def record_viewer_join(
    channel: str, stream_session_id: str | None, username: str
) -> dict:
    vid = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO viewer_sessions
               (id, channel, stream_session_id, username, joined_at, duration_seconds, messages_sent)
               VALUES (%s,%s,%s,%s,%s,0,0)""",
            (vid, channel, stream_session_id, username, now),
        )
        await conn.commit()
    return {
        "id": vid, "channel": channel, "stream_session_id": stream_session_id,
        "username": username, "joined_at": now, "left_at": None,
        "duration_seconds": 0, "messages_sent": 0,
    }


async def record_viewer_leave(session_id: str, duration_seconds: int) -> bool:
    now = _now_iso()
    async with get_conn() as conn:
        result = await conn.execute(
            "UPDATE viewer_sessions SET left_at = %s, duration_seconds = %s WHERE id = %s",
            (now, duration_seconds, session_id),
        )
        await conn.commit()
        return result.rowcount > 0


async def get_viewer_sessions(channel: str, stream_session_id: str | None = None, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        if stream_session_id:
            cur = await conn.execute(
                """SELECT * FROM viewer_sessions
                   WHERE channel = %s AND stream_session_id = %s
                   ORDER BY joined_at DESC LIMIT %s""",
                (channel, stream_session_id, limit),
            )
        else:
            cur = await conn.execute(
                "SELECT * FROM viewer_sessions WHERE channel = %s ORDER BY joined_at DESC LIMIT %s",
                (channel, limit),
            )
        return [dict(r) for r in await cur.fetchall()]


async def get_viewer_stats(channel: str) -> dict:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT
                 count(*) AS total_sessions,
                 coalesce(avg(duration_seconds), 0) AS avg_duration,
                 coalesce(sum(messages_sent), 0) AS total_messages,
                 count(DISTINCT username) AS unique_viewers
               FROM viewer_sessions WHERE channel = %s""",
            (channel,),
        )
        row = await cur.fetchone()
    return dict(row) if row else {
        "total_sessions": 0, "avg_duration": 0, "total_messages": 0, "unique_viewers": 0,
    }


# ---------------------------------------------------------------------------
# Content Segments
# ---------------------------------------------------------------------------

async def create_segment(
    channel: str,
    stream_session_id: str,
    label: str,
    category: str,
    started_at: str,
    ended_at: str | None,
    viewer_count_start: int,
    viewer_count_end: int,
) -> dict:
    seg_id = _generate_id()
    avg_viewers = (viewer_count_start + viewer_count_end) / 2 if viewer_count_end > 0 else float(viewer_count_start)
    retention = (viewer_count_end / viewer_count_start * 100) if viewer_count_start > 0 else 0.0
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO content_segments
               (id, channel, stream_session_id, label, category, started_at, ended_at,
                viewer_count_start, viewer_count_end, avg_viewers, retention_rate, chat_activity)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)""",
            (seg_id, channel, stream_session_id, label, category,
             started_at, ended_at, viewer_count_start, viewer_count_end,
             round(avg_viewers, 1), round(retention, 1)),
        )
        await conn.commit()
    return {
        "id": seg_id, "channel": channel, "stream_session_id": stream_session_id,
        "label": label, "category": category, "started_at": started_at,
        "ended_at": ended_at, "viewer_count_start": viewer_count_start,
        "viewer_count_end": viewer_count_end, "avg_viewers": round(avg_viewers, 1),
        "retention_rate": round(retention, 1), "chat_activity": 0,
    }


async def get_segments(stream_session_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM content_segments WHERE stream_session_id = %s ORDER BY started_at ASC",
            (stream_session_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_category_stats(channel: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT category,
                 count(*) AS segment_count,
                 coalesce(avg(avg_viewers), 0) AS avg_viewers,
                 coalesce(avg(retention_rate), 0) AS avg_retention,
                 coalesce(sum(chat_activity), 0) AS total_chat
               FROM content_segments
               WHERE channel = %s
               GROUP BY category
               ORDER BY avg_viewers DESC""",
            (channel,),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Heatmap Snapshots
# ---------------------------------------------------------------------------

async def record_heatmap_snapshot(
    channel: str,
    stream_session_id: str,
    minute_offset: int,
    viewer_count: int,
    message_count: int,
    unique_chatters: int,
    category: str,
) -> None:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO heatmap_snapshots
               (channel, stream_session_id, minute_offset, viewer_count,
                message_count, unique_chatters, category, recorded_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (channel, stream_session_id, minute_offset, viewer_count,
             message_count, unique_chatters, category, now),
        )
        await conn.commit()


async def get_heatmap_timeline(stream_session_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM heatmap_snapshots
               WHERE stream_session_id = %s ORDER BY minute_offset ASC""",
            (stream_session_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_aggregate_heatmap(channel: str, limit_sessions: int = 10) -> list[dict]:
    """Get averaged heatmap data across recent sessions."""
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT minute_offset,
                 avg(viewer_count) AS avg_viewers,
                 avg(message_count) AS avg_messages,
                 avg(unique_chatters) AS avg_chatters
               FROM heatmap_snapshots
               WHERE channel = %s
               AND stream_session_id IN (
                   SELECT DISTINCT stream_session_id FROM heatmap_snapshots
                   WHERE channel = %s
                   ORDER BY stream_session_id DESC
                   LIMIT %s
               )
               GROUP BY minute_offset
               ORDER BY minute_offset ASC""",
            (channel, channel, limit_sessions),
        )
        return [dict(r) for r in await cur.fetchall()]
