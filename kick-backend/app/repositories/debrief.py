"""Repository for AI post-stream debriefs."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def create_debrief(
    channel: str, stream_date: str,
    session_id: Optional[str] = None, duration_minutes: int = 0,
) -> dict:
    debrief_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO stream_debriefs
               (id, channel, session_id, stream_date, duration_minutes, status, created_at)
               VALUES (%s, %s, %s, %s, %s, 'pending', %s)""",
            (debrief_id, channel, session_id, stream_date, duration_minutes, now),
        )
        await conn.commit()
    return {
        "id": debrief_id, "channel": channel, "session_id": session_id,
        "stream_date": stream_date, "duration_minutes": duration_minutes,
        "summary": "", "highlights": [], "lowlights": [],
        "chat_sentiment_summary": "", "top_moments": [],
        "recommendations": [], "viewer_feedback": "",
        "mood_timeline": [], "status": "pending", "created_at": now,
    }


async def get_debrief(debrief_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_debriefs WHERE id = %s", (debrief_id,)
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        for field in ("highlights", "lowlights", "top_moments", "recommendations", "mood_timeline"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        return d
    return None


async def update_debrief(debrief_id: str, **kwargs: object) -> Optional[dict]:
    if not kwargs:
        return None
    set_parts = []
    values: list[object] = []
    for key, val in kwargs.items():
        if isinstance(val, (list, dict)):
            val = json.dumps(val)
        set_parts.append(f"{key} = %s")
        values.append(val)
    values.append(debrief_id)
    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE stream_debriefs SET {', '.join(set_parts)} WHERE id = %s",
            tuple(values),
        )
        await conn.commit()
    return await get_debrief(debrief_id)


async def list_debriefs(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM stream_debriefs WHERE channel = %s
               ORDER BY stream_date DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    out = []
    for r in results:
        d = dict(r)
        for field in ("highlights", "lowlights", "top_moments", "recommendations", "mood_timeline"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        out.append(d)
    return out


async def delete_debrief(debrief_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM stream_debriefs WHERE id = %s", (debrief_id,)
        )
        await conn.commit()


async def get_debrief_by_session(session_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM stream_debriefs WHERE session_id = %s ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        for field in ("highlights", "lowlights", "top_moments", "recommendations", "mood_timeline"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        return d
    return None
