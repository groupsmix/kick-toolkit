"""Repository for viewer CRM — profiles, segments, churn detection."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Viewer Profiles
# ---------------------------------------------------------------------------

async def get_profile(channel: str, username: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM viewer_profiles WHERE channel = %s AND username = %s",
            (channel, username),
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        if isinstance(d.get("favorite_games"), str):
            d["favorite_games"] = json.loads(d["favorite_games"])
        return d
    return None


async def upsert_profile(
    channel: str, username: str,
    total_messages: int = 0, total_watch_minutes: int = 0,
    streams_attended: int = 0, is_subscriber: bool = False,
    is_follower: bool = False, is_moderator: bool = False,
    favorite_games: Optional[list[str]] = None,
) -> dict:
    now = _now_iso()
    profile_id = _generate_id()
    games_json = json.dumps(favorite_games or [])
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO viewer_profiles
               (id, channel, username, first_seen, last_seen, total_messages,
                total_watch_minutes, streams_attended, is_subscriber, is_follower,
                is_moderator, favorite_games, segment, notes, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'new', '', %s)
               ON CONFLICT (channel, username) DO UPDATE SET
                   last_seen = EXCLUDED.last_seen,
                   total_messages = viewer_profiles.total_messages + EXCLUDED.total_messages,
                   total_watch_minutes = viewer_profiles.total_watch_minutes + EXCLUDED.total_watch_minutes,
                   streams_attended = viewer_profiles.streams_attended + EXCLUDED.streams_attended,
                   is_subscriber = EXCLUDED.is_subscriber,
                   is_follower = EXCLUDED.is_follower,
                   is_moderator = EXCLUDED.is_moderator,
                   updated_at = EXCLUDED.updated_at""",
            (profile_id, channel, username, now, now, total_messages,
             total_watch_minutes, streams_attended, is_subscriber, is_follower,
             is_moderator, games_json, now),
        )
        await conn.commit()

        row = await conn.execute(
            "SELECT * FROM viewer_profiles WHERE channel = %s AND username = %s",
            (channel, username),
        )
        result = await row.fetchone()
    d = dict(result) if result else {}
    if isinstance(d.get("favorite_games"), str):
        d["favorite_games"] = json.loads(d["favorite_games"])
    return d


async def update_profile(channel: str, username: str, **kwargs: object) -> Optional[dict]:
    if not kwargs:
        return None
    set_parts = []
    values: list[object] = []
    for key, val in kwargs.items():
        set_parts.append(f"{key} = %s")
        values.append(val)
    set_parts.append("updated_at = %s")
    values.append(_now_iso())
    values.extend([channel, username])
    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE viewer_profiles SET {', '.join(set_parts)} WHERE channel = %s AND username = %s",
            tuple(values),
        )
        await conn.commit()
        row = await conn.execute(
            "SELECT * FROM viewer_profiles WHERE channel = %s AND username = %s",
            (channel, username),
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        if isinstance(d.get("favorite_games"), str):
            d["favorite_games"] = json.loads(d["favorite_games"])
        return d
    return None


async def list_profiles(
    channel: str, segment: Optional[str] = None,
    sort_by: str = "last_seen", limit: int = 50, offset: int = 0,
) -> list[dict]:
    allowed_sorts = {"last_seen", "total_messages", "streams_attended", "total_watch_minutes", "first_seen"}
    if sort_by not in allowed_sorts:
        sort_by = "last_seen"

    query = "SELECT * FROM viewer_profiles WHERE channel = %s"
    params: list[object] = [channel]
    if segment:
        query += " AND segment = %s"
        params.append(segment)
    query += f" ORDER BY {sort_by} DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    async with get_conn() as conn:
        row = await conn.execute(query, tuple(params))
        results = await row.fetchall()
    out = []
    for r in results:
        d = dict(r)
        if isinstance(d.get("favorite_games"), str):
            d["favorite_games"] = json.loads(d["favorite_games"])
        out.append(d)
    return out


async def get_segment_summary(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT segment,
                      COUNT(*) AS count,
                      AVG(total_messages) AS avg_messages,
                      AVG(total_watch_minutes) AS avg_watch_minutes
               FROM viewer_profiles WHERE channel = %s
               GROUP BY segment ORDER BY count DESC""",
            (channel,),
        )
        results = await row.fetchall()
    return [
        {
            "segment": r["segment"],
            "count": int(r["count"]),
            "avg_messages": round(float(r["avg_messages"]), 1),
            "avg_watch_minutes": round(float(r["avg_watch_minutes"]), 1),
        }
        for r in results
    ]


async def get_churn_risks(channel: str, days_threshold: int = 7, limit: int = 20) -> list[dict]:
    """Find viewers who used to be active but haven't been seen recently."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT username, last_seen, total_messages, streams_attended, segment
               FROM viewer_profiles
               WHERE channel = %s
                 AND streams_attended >= 3
                 AND last_seen < NOW() - INTERVAL '%s days'
               ORDER BY streams_attended DESC LIMIT %s""",
            (channel, days_threshold, limit),
        )
        results = await row.fetchall()
    out = []
    for r in results:
        out.append({
            "username": r["username"],
            "channel": channel,
            "last_seen": r["last_seen"],
            "days_absent": days_threshold,
            "previous_frequency": "daily" if r["streams_attended"] > 20 else "weekly" if r["streams_attended"] > 5 else "occasional",
            "risk_level": "high" if r["streams_attended"] > 10 else "medium",
            "total_messages": r["total_messages"],
            "streams_attended": r["streams_attended"],
        })
    return out


async def get_shoutout_suggestions(channel: str, limit: int = 10) -> list[dict]:
    """Find loyal viewers who deserve recognition."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT username, total_messages, streams_attended
               FROM viewer_profiles
               WHERE channel = %s AND streams_attended >= 5
               ORDER BY streams_attended DESC, total_messages DESC
               LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [
        {
            "username": r["username"],
            "reason": f"Attended {r['streams_attended']} streams with {r['total_messages']} messages",
            "streams_attended": r["streams_attended"],
            "total_messages": r["total_messages"],
            "last_acknowledged": None,
        }
        for r in results
    ]


async def get_viewer_count(channel: str) -> int:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM viewer_profiles WHERE channel = %s",
            (channel,),
        )
        result = await row.fetchone()
    return result["cnt"] if result else 0
