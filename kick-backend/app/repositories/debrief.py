"""Repository for AI Post-Stream Debrief data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


def _parse_debrief(row: dict) -> dict:
    d = dict(row)
    for field in ("top_moments", "sentiment_timeline", "chat_highlights",
                  "recommendations", "title_suggestions", "trending_topics"):
        if isinstance(d.get(field), str):
            d[field] = json.loads(d[field])
    return d


async def create_debrief(
    channel: str,
    session_id: str | None = None,
    summary: str = "",
    top_moments: list[dict] | None = None,
    sentiment_timeline: list[dict] | None = None,
    chat_highlights: list[str] | None = None,
    recommendations: list[str] | None = None,
    title_suggestions: list[str] | None = None,
    trending_topics: list[str] | None = None,
) -> dict:
    did = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO debrief_results
               (id, channel, session_id, summary, top_moments, sentiment_timeline,
                chat_highlights, recommendations, title_suggestions, trending_topics, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (did, channel, session_id, summary,
             json.dumps(top_moments or []), json.dumps(sentiment_timeline or []),
             json.dumps(chat_highlights or []), json.dumps(recommendations or []),
             json.dumps(title_suggestions or []), json.dumps(trending_topics or []),
             now),
        )
        await conn.commit()
    return {
        "id": did, "channel": channel, "session_id": session_id,
        "summary": summary, "top_moments": top_moments or [],
        "sentiment_timeline": sentiment_timeline or [],
        "chat_highlights": chat_highlights or [],
        "recommendations": recommendations or [],
        "title_suggestions": title_suggestions or [],
        "trending_topics": trending_topics or [], "created_at": now,
    }


async def get_debriefs(channel: str, limit: int = 10) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM debrief_results
               WHERE channel = %s ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        rows = await cur.fetchall()
    return [_parse_debrief(r) for r in rows]


async def get_debrief(debrief_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM debrief_results WHERE id = %s", (debrief_id,),
        )
        row = await cur.fetchone()
    if row:
        return _parse_debrief(row)
    return None


async def get_debrief_by_session(channel: str, session_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM debrief_results WHERE channel = %s AND session_id = %s ORDER BY created_at DESC LIMIT 1",
            (channel, session_id),
        )
        row = await cur.fetchone()
    if row:
        return _parse_debrief(row)
    return None
