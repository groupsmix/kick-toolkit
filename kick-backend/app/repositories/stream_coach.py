"""Repository for AI Stream Coach data access."""


from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Coach Settings
# ---------------------------------------------------------------------------

async def get_settings(channel: str) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM coach_settings WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    if result:
        return dict(result)
    return {
        "channel": channel,
        "enabled": True,
        "engagement_alerts": True,
        "game_duration_alerts": True,
        "viewer_change_alerts": True,
        "raid_welcome_alerts": True,
        "sentiment_alerts": True,
        "break_reminders": True,
        "break_reminder_minutes": 120,
        "engagement_drop_threshold": 30.0,
        "viewer_change_threshold": 10,
    }


async def upsert_settings(
    channel: str,
    enabled: bool,
    engagement_alerts: bool,
    game_duration_alerts: bool,
    viewer_change_alerts: bool,
    raid_welcome_alerts: bool,
    sentiment_alerts: bool,
    break_reminders: bool,
    break_reminder_minutes: int,
    engagement_drop_threshold: float,
    viewer_change_threshold: int,
) -> None:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO coach_settings (
                channel, enabled, engagement_alerts, game_duration_alerts,
                viewer_change_alerts, raid_welcome_alerts, sentiment_alerts,
                break_reminders, break_reminder_minutes,
                engagement_drop_threshold, viewer_change_threshold
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (channel) DO UPDATE SET
                enabled = EXCLUDED.enabled,
                engagement_alerts = EXCLUDED.engagement_alerts,
                game_duration_alerts = EXCLUDED.game_duration_alerts,
                viewer_change_alerts = EXCLUDED.viewer_change_alerts,
                raid_welcome_alerts = EXCLUDED.raid_welcome_alerts,
                sentiment_alerts = EXCLUDED.sentiment_alerts,
                break_reminders = EXCLUDED.break_reminders,
                break_reminder_minutes = EXCLUDED.break_reminder_minutes,
                engagement_drop_threshold = EXCLUDED.engagement_drop_threshold,
                viewer_change_threshold = EXCLUDED.viewer_change_threshold
            """,
            (
                channel, enabled, engagement_alerts, game_duration_alerts,
                viewer_change_alerts, raid_welcome_alerts, sentiment_alerts,
                break_reminders, break_reminder_minutes,
                engagement_drop_threshold, viewer_change_threshold,
            ),
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Stream Sessions
# ---------------------------------------------------------------------------

async def create_session(channel: str, game: str = "") -> dict:
    session_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_sessions (id, channel, status, started_at, game)
               VALUES (%s, %s, 'active', %s, %s)""",
            (session_id, channel, now, game),
        )
        await conn.commit()
    return {
        "id": session_id,
        "channel": channel,
        "status": "active",
        "started_at": now,
        "ended_at": None,
        "peak_viewers": 0,
        "avg_viewers": 0.0,
        "total_messages": 0,
        "game": game,
    }


async def get_active_session(channel: str) -> dict | None:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_sessions WHERE channel = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def end_session(session_id: str) -> dict | None:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE stream_sessions SET status = 'ended', ended_at = %s WHERE id = %s",
            (now, session_id),
        )
        await conn.commit()
        row = await conn.execute(
            "SELECT * FROM stream_sessions WHERE id = %s", (session_id,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def update_session_stats(
    session_id: str, peak_viewers: int, avg_viewers: float, total_messages: int, game: str
) -> None:
    async with get_conn() as conn:
        await conn.execute(
            """UPDATE stream_sessions
               SET peak_viewers = %s, avg_viewers = %s, total_messages = %s, game = %s
               WHERE id = %s""",
            (peak_viewers, avg_viewers, total_messages, game, session_id),
        )
        await conn.commit()


async def get_session(session_id: str) -> dict | None:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_sessions WHERE id = %s", (session_id,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def list_sessions(channel: str, limit: int = 10) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_sessions WHERE channel = %s ORDER BY started_at DESC LIMIT %s",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


# ---------------------------------------------------------------------------
# Coach Suggestions
# ---------------------------------------------------------------------------

async def create_suggestion(
    session_id: str,
    channel: str,
    suggestion_type: str,
    priority: str,
    title: str,
    message: str,
) -> dict:
    suggestion_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO coach_suggestions (id, session_id, channel, type, priority, title, message, dismissed, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, %s)""",
            (suggestion_id, session_id, channel, suggestion_type, priority, title, message, now),
        )
        await conn.commit()
    return {
        "id": suggestion_id,
        "session_id": session_id,
        "channel": channel,
        "type": suggestion_type,
        "priority": priority,
        "title": title,
        "message": message,
        "dismissed": False,
        "created_at": now,
        "dismissed_at": None,
    }


async def get_suggestions(
    session_id: str, include_dismissed: bool = False
) -> list[dict]:
    async with get_conn() as conn:
        if include_dismissed:
            row = await conn.execute(
                "SELECT * FROM coach_suggestions WHERE session_id = %s ORDER BY created_at DESC",
                (session_id,),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM coach_suggestions WHERE session_id = %s AND dismissed = FALSE ORDER BY created_at DESC",
                (session_id,),
            )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_suggestion(suggestion_id: str) -> dict | None:
    """Return a single suggestion by ID, or None."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM coach_suggestions WHERE id = %s", (suggestion_id,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def dismiss_suggestion(suggestion_id: str) -> bool:
    now = _now_iso()
    async with get_conn() as conn:
        result = await conn.execute(
            "UPDATE coach_suggestions SET dismissed = TRUE, dismissed_at = %s WHERE id = %s AND dismissed = FALSE",
            (now, suggestion_id),
        )
        await conn.commit()
        return result.rowcount > 0


async def dismiss_all_suggestions(session_id: str) -> int:
    now = _now_iso()
    async with get_conn() as conn:
        result = await conn.execute(
            "UPDATE coach_suggestions SET dismissed = TRUE, dismissed_at = %s WHERE session_id = %s AND dismissed = FALSE",
            (now, session_id),
        )
        await conn.commit()
        return result.rowcount


# ---------------------------------------------------------------------------
# Stream Snapshots (for tracking metrics over time)
# ---------------------------------------------------------------------------

async def record_snapshot(
    session_id: str, channel: str, viewer_count: int, message_count: int, game: str
) -> None:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_snapshots (session_id, channel, viewer_count, message_count, game, recorded_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (session_id, channel, viewer_count, message_count, game, now),
        )
        await conn.commit()


async def get_snapshots(session_id: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_snapshots WHERE session_id = %s ORDER BY recorded_at ASC",
            (session_id,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_recent_message_rate(channel: str, minutes: int = 5) -> dict:
    """Get message count and unique chatters in the last N minutes."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT count(*) AS msg_count, count(DISTINCT username) AS unique_chatters
               FROM chat_logs
               WHERE channel = %s
               AND timestamp >= (NOW() - INTERVAL '%s minutes')::text""",
            (channel, minutes),
        )
        result = await row.fetchone()
    return dict(result) if result else {"msg_count": 0, "unique_chatters": 0}


async def get_chat_activity_trend(channel: str, window_minutes: int = 30) -> list[dict]:
    """Get chat message counts grouped into 5-minute buckets over the last N minutes."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT
                 date_trunc('minute', timestamp::timestamptz) -
                 (EXTRACT(MINUTE FROM timestamp::timestamptz)::int %% 5) * INTERVAL '1 minute' AS bucket,
                 count(*) AS msg_count,
                 count(DISTINCT username) AS unique_chatters
               FROM chat_logs
               WHERE channel = %s
               AND timestamp >= (NOW() - INTERVAL '%s minutes')::text
               GROUP BY bucket
               ORDER BY bucket ASC""",
            (channel, window_minutes),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]
