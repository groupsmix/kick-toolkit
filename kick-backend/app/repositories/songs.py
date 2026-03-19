"""Repository for song request queue management."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_settings(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM song_queue_settings WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_settings(
    channel: str,
    enabled: bool,
    max_queue_size: int,
    max_duration_seconds: int,
    allow_duplicates: bool,
    subscriber_only: bool,
    cost_per_request: int,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO song_queue_settings
               (channel, enabled, max_queue_size, max_duration_seconds,
                allow_duplicates, subscriber_only, cost_per_request, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   enabled = EXCLUDED.enabled, max_queue_size = EXCLUDED.max_queue_size,
                   max_duration_seconds = EXCLUDED.max_duration_seconds,
                   allow_duplicates = EXCLUDED.allow_duplicates,
                   subscriber_only = EXCLUDED.subscriber_only,
                   cost_per_request = EXCLUDED.cost_per_request,
                   updated_at = EXCLUDED.updated_at""",
            (channel, enabled, max_queue_size, max_duration_seconds,
             allow_duplicates, subscriber_only, cost_per_request, now),
        )
        await conn.commit()
    return {
        "channel": channel, "enabled": enabled, "max_queue_size": max_queue_size,
        "max_duration_seconds": max_duration_seconds, "allow_duplicates": allow_duplicates,
        "subscriber_only": subscriber_only, "cost_per_request": cost_per_request,
        "updated_at": now,
    }


async def get_queue(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM song_requests WHERE channel = %s AND status IN ('queued', 'playing')
               ORDER BY position ASC""",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def add_request(
    channel: str, username: str, title: str, artist: str,
    url: Optional[str], platform: str, duration_seconds: int,
) -> dict:
    song_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        # Get next position
        row = await conn.execute(
            """SELECT COALESCE(MAX(position), 0) + 1 AS next_pos
               FROM song_requests WHERE channel = %s AND status IN ('queued', 'playing')""",
            (channel,),
        )
        pos_row = await row.fetchone()
        position = pos_row["next_pos"] if pos_row else 1

        await conn.execute(
            """INSERT INTO song_requests
               (id, channel, username, title, artist, url, platform, duration_seconds, status, position, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'queued', %s, %s)""",
            (song_id, channel, username, title, artist, url, platform, duration_seconds, position, now),
        )
        await conn.commit()
    return {
        "id": song_id, "channel": channel, "username": username, "title": title,
        "artist": artist, "url": url, "platform": platform,
        "duration_seconds": duration_seconds, "status": "queued",
        "position": position, "created_at": now,
    }


async def skip_song(channel: str, song_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE song_requests SET status = 'skipped'
               WHERE id = %s AND channel = %s RETURNING *""",
            (song_id, channel),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def play_song(channel: str, song_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        # Set any currently playing to played
        await conn.execute(
            "UPDATE song_requests SET status = 'played' WHERE channel = %s AND status = 'playing'",
            (channel,),
        )
        row = await conn.execute(
            """UPDATE song_requests SET status = 'playing'
               WHERE id = %s AND channel = %s RETURNING *""",
            (song_id, channel),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def clear_queue(channel: str) -> int:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE song_requests SET status = 'skipped'
               WHERE channel = %s AND status = 'queued'""",
            (channel,),
        )
        count = row.rowcount
        await conn.commit()
    return count


async def get_history(channel: str, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM song_requests WHERE channel = %s AND status IN ('played', 'skipped')
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def remove_request(channel: str, song_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM song_requests WHERE id = %s AND channel = %s AND status = 'queued'",
            (song_id, channel),
        )
        await conn.commit()
