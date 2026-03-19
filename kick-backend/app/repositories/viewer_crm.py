"""Repository for Viewer CRM data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


def _parse_json_field(row: dict, field: str) -> dict:
    d = dict(row)
    if isinstance(d.get(field), str):
        d[field] = json.loads(d[field])
    return d


async def get_viewers(channel: str, segment: str | None = None, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        if segment:
            cur = await conn.execute(
                """SELECT * FROM viewer_profiles
                   WHERE channel = %s AND segment = %s
                   ORDER BY total_messages DESC LIMIT %s""",
                (channel, segment, limit),
            )
        else:
            cur = await conn.execute(
                """SELECT * FROM viewer_profiles
                   WHERE channel = %s
                   ORDER BY total_messages DESC LIMIT %s""",
                (channel, limit),
            )
        rows = await cur.fetchall()
    return [_parse_json_field(r, "favorite_games") for r in rows]


async def get_viewer(channel: str, username: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM viewer_profiles WHERE channel = %s AND username = %s",
            (channel, username),
        )
        row = await cur.fetchone()
    if row:
        return _parse_json_field(row, "favorite_games")
    return None


async def upsert_viewer(
    channel: str,
    username: str,
    total_messages: int = 0,
    streams_watched: int = 0,
    is_subscriber: bool = False,
    is_follower: bool = False,
    watch_time_minutes: int = 0,
    favorite_games: list[str] | None = None,
) -> dict:
    now = _now_iso()
    existing = await get_viewer(channel, username)
    if existing:
        async with get_conn() as conn:
            await conn.execute(
                """UPDATE viewer_profiles SET
                   last_seen = %s, total_messages = %s, streams_watched = %s,
                   is_subscriber = %s, is_follower = %s, watch_time_minutes = %s,
                   favorite_games = %s
                   WHERE channel = %s AND username = %s""",
                (now, total_messages, streams_watched, is_subscriber, is_follower,
                 watch_time_minutes, json.dumps(favorite_games or []), channel, username),
            )
            await conn.commit()
        existing.update({
            "last_seen": now, "total_messages": total_messages,
            "streams_watched": streams_watched, "is_subscriber": is_subscriber,
            "is_follower": is_follower, "watch_time_minutes": watch_time_minutes,
            "favorite_games": favorite_games or [],
        })
        return existing
    else:
        vid = _generate_id()
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO viewer_profiles
                   (id, channel, username, first_seen, last_seen, total_messages,
                    streams_watched, is_subscriber, is_follower, segment,
                    watch_time_minutes, favorite_games, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (vid, channel, username, now, now, total_messages, streams_watched,
                 is_subscriber, is_follower, "new", watch_time_minutes,
                 json.dumps(favorite_games or []), ""),
            )
            await conn.commit()
        return {
            "id": vid, "channel": channel, "username": username,
            "first_seen": now, "last_seen": now, "total_messages": total_messages,
            "streams_watched": streams_watched, "is_subscriber": is_subscriber,
            "is_follower": is_follower, "segment": "new",
            "watch_time_minutes": watch_time_minutes,
            "favorite_games": favorite_games or [], "notes": "",
        }


async def update_viewer(channel: str, username: str, notes: str | None = None, segment: str | None = None) -> dict | None:
    existing = await get_viewer(channel, username)
    if not existing:
        return None
    updates = []
    params: list = []
    if notes is not None:
        updates.append("notes = %s")
        params.append(notes)
    if segment is not None:
        updates.append("segment = %s")
        params.append(segment)
    if not updates:
        return existing
    params.extend([channel, username])
    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE viewer_profiles SET {', '.join(updates)} WHERE channel = %s AND username = %s",
            tuple(params),
        )
        await conn.commit()
    return await get_viewer(channel, username)


async def get_segment_summary(channel: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT segment, COUNT(*) as count,
                      AVG(total_messages) as avg_messages,
                      AVG(streams_watched) as avg_streams_watched
               FROM viewer_profiles WHERE channel = %s
               GROUP BY segment ORDER BY count DESC""",
            (channel,),
        )
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_overview(channel: str) -> dict:
    segments = await get_segment_summary(channel)
    top_viewers = await get_viewers(channel, limit=10)
    at_risk = await get_viewers(channel, segment="at_risk", limit=10)

    # Shoutout suggestions: regular viewers with high activity but not super_fans
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM viewer_profiles
               WHERE channel = %s AND segment IN ('regular', 'new')
               AND streams_watched >= 3 AND total_messages >= 10
               ORDER BY streams_watched DESC LIMIT 5""",
            (channel,),
        )
        shoutout_rows = await cur.fetchall()
    shoutouts = [_parse_json_field(r, "favorite_games") for r in shoutout_rows]

    # Total viewers
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT COUNT(*) as cnt FROM viewer_profiles WHERE channel = %s",
            (channel,),
        )
        total_row = await cur.fetchone()
    total = total_row["cnt"] if total_row else 0

    # Churn predictions: viewers who haven't been seen recently
    churn = []
    for v in at_risk:
        churn.append({
            "username": v["username"],
            "last_seen": v["last_seen"],
            "streams_watched": v["streams_watched"],
            "risk_level": "high" if v["streams_watched"] > 10 else "medium",
            "suggestion": "Send a shoutout or DM" if v["streams_watched"] > 10 else "Engage in chat",
        })

    return {
        "channel": channel,
        "total_viewers": total,
        "segments": segments,
        "top_viewers": top_viewers,
        "at_risk_viewers": at_risk,
        "shoutout_suggestions": shoutouts,
        "churn_predictions": churn,
    }
