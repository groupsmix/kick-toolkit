"""Repository for AI Clip Pipeline data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Hype Moments
# ---------------------------------------------------------------------------

async def create_hype_moment(
    channel: str,
    session_id: str | None,
    timestamp_start: str,
    timestamp_end: str,
    intensity: float,
    trigger_type: str,
    message_count: int,
    peak_rate: float,
    sample_messages: list[str],
) -> dict:
    moment_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO hype_moments
               (id, channel, session_id, timestamp_start, timestamp_end,
                intensity, trigger_type, message_count, peak_rate, sample_messages, status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'detected',%s)""",
            (moment_id, channel, session_id, timestamp_start, timestamp_end,
             intensity, trigger_type, message_count, peak_rate,
             json.dumps(sample_messages), now),
        )
        await conn.commit()
    return {
        "id": moment_id, "channel": channel, "session_id": session_id,
        "timestamp_start": timestamp_start, "timestamp_end": timestamp_end,
        "intensity": intensity, "trigger_type": trigger_type,
        "message_count": message_count, "peak_rate": peak_rate,
        "sample_messages": sample_messages, "status": "detected",
        "created_at": now,
    }


async def get_hype_moments(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM hype_moments WHERE channel = %s ORDER BY created_at DESC LIMIT %s",
            (channel, limit),
        )
        rows = await cur.fetchall()
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("sample_messages"), str):
            d["sample_messages"] = json.loads(d["sample_messages"])
        results.append(d)
    return results


async def get_hype_moment(moment_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM hype_moments WHERE id = %s", (moment_id,)
        )
        row = await cur.fetchone()
    if row:
        d = dict(row)
        if isinstance(d.get("sample_messages"), str):
            d["sample_messages"] = json.loads(d["sample_messages"])
        return d
    return None


async def update_hype_moment_status(moment_id: str, status: str) -> bool:
    async with get_conn() as conn:
        result = await conn.execute(
            "UPDATE hype_moments SET status = %s WHERE id = %s",
            (status, moment_id),
        )
        await conn.commit()
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Generated Clips
# ---------------------------------------------------------------------------

async def create_clip(
    channel: str,
    hype_moment_id: str | None,
    title: str,
    description: str,
    duration_seconds: float,
) -> dict:
    clip_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO generated_clips
               (id, channel, hype_moment_id, title, description, caption,
                duration_seconds, status, platform_specs, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,'',%s,'pending','{}', %s,%s)""",
            (clip_id, channel, hype_moment_id, title, description,
             duration_seconds, now, now),
        )
        await conn.commit()
    return {
        "id": clip_id, "channel": channel, "hype_moment_id": hype_moment_id,
        "title": title, "description": description, "caption": "",
        "file_path": None, "thumbnail_path": None,
        "duration_seconds": duration_seconds, "status": "pending",
        "platform_specs": {}, "created_at": now, "updated_at": now,
    }


async def get_clip(clip_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM generated_clips WHERE id = %s", (clip_id,)
        )
        row = await cur.fetchone()
    if row:
        d = dict(row)
        if isinstance(d.get("platform_specs"), str):
            d["platform_specs"] = json.loads(d["platform_specs"])
        return d
    return None


async def list_clips(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM generated_clips WHERE channel = %s ORDER BY created_at DESC LIMIT %s",
            (channel, limit),
        )
        rows = await cur.fetchall()
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("platform_specs"), str):
            d["platform_specs"] = json.loads(d["platform_specs"])
        results.append(d)
    return results


async def update_clip(clip_id: str, **kwargs: object) -> dict | None:
    now = _now_iso()
    allowed = {"title", "description", "caption", "file_path", "thumbnail_path",
               "duration_seconds", "status", "platform_specs"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return await get_clip(clip_id)

    set_parts = [f"{k} = %s" for k in updates]
    set_parts.append("updated_at = %s")
    values = list(updates.values())
    if "platform_specs" in updates and isinstance(updates["platform_specs"], dict):
        idx = list(updates.keys()).index("platform_specs")
        values[idx] = json.dumps(updates["platform_specs"])
    values.append(now)
    values.append(clip_id)

    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE generated_clips SET {', '.join(set_parts)} WHERE id = %s",
            tuple(values),
        )
        await conn.commit()
    return await get_clip(clip_id)


async def delete_clip(clip_id: str) -> bool:
    async with get_conn() as conn:
        result = await conn.execute(
            "DELETE FROM generated_clips WHERE id = %s", (clip_id,)
        )
        await conn.commit()
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Clip Posts
# ---------------------------------------------------------------------------

async def create_clip_post(
    clip_id: str,
    platform: str,
    caption: str,
) -> dict:
    post_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO clip_posts
               (id, clip_id, platform, status, caption, created_at)
               VALUES (%s,%s,%s,'pending',%s,%s)""",
            (post_id, clip_id, platform, caption, now),
        )
        await conn.commit()
    return {
        "id": post_id, "clip_id": clip_id, "platform": platform,
        "platform_post_id": None, "post_url": None, "status": "pending",
        "caption": caption, "error_message": None, "posted_at": None,
        "created_at": now,
    }


async def get_clip_posts(clip_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM clip_posts WHERE clip_id = %s ORDER BY created_at DESC",
            (clip_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def update_clip_post(post_id: str, status: str, post_url: str | None = None,
                           platform_post_id: str | None = None,
                           error_message: str | None = None) -> bool:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """UPDATE clip_posts SET status = %s, post_url = %s,
               platform_post_id = %s, error_message = %s, posted_at = %s
               WHERE id = %s""",
            (status, post_url, platform_post_id, error_message, now, post_id),
        )
        await conn.commit()
        return True
