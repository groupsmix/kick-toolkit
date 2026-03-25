"""Repository for Auto-Highlight Detection data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


def _parse_highlight(row: dict) -> dict:
    d = dict(row)
    if isinstance(d.get("sample_messages"), str):
        d["sample_messages"] = json.loads(d["sample_messages"])
    return d


async def create_highlight(
    channel: str,
    session_id: str | None = None,
    timestamp_offset_seconds: int = 0,
    intensity: float = 0.0,
    message_rate: float = 0.0,
    duration_seconds: int = 30,
    description: str = "",
    sample_messages: list[str] | None = None,
    category: str = "hype",
) -> dict:
    hid = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO highlight_markers
               (id, channel, session_id, timestamp_offset_seconds, intensity,
                message_rate, duration_seconds, description, sample_messages,
                category, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (hid, channel, session_id, timestamp_offset_seconds, intensity,
             message_rate, duration_seconds, description,
             json.dumps(sample_messages or []), category, now),
        )
        await conn.commit()
    return {
        "id": hid, "channel": channel, "session_id": session_id,
        "timestamp_offset_seconds": timestamp_offset_seconds,
        "intensity": intensity, "message_rate": message_rate,
        "duration_seconds": duration_seconds, "description": description,
        "sample_messages": sample_messages or [], "category": category,
        "created_at": now,
    }


async def get_highlights(channel: str, session_id: str | None = None, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        if session_id:
            cur = await conn.execute(
                """SELECT * FROM highlight_markers
                   WHERE channel = %s AND session_id = %s
                   ORDER BY intensity DESC LIMIT %s""",
                (channel, session_id, limit),
            )
        else:
            cur = await conn.execute(
                """SELECT * FROM highlight_markers
                   WHERE channel = %s
                   ORDER BY created_at DESC, intensity DESC LIMIT %s""",
                (channel, limit),
            )
        rows = await cur.fetchall()
    return [_parse_highlight(r) for r in rows]


async def get_summary(channel: str, session_id: str | None = None) -> dict:
    highlights = await get_highlights(channel, session_id=session_id, limit=100)
    peak = max(highlights, key=lambda h: h["intensity"]) if highlights else None
    return {
        "channel": channel,
        "session_id": session_id,
        "total_highlights": len(highlights),
        "peak_moment": peak,
        "highlights": highlights,
        "stream_summary": _generate_summary(highlights),
    }


def _generate_summary(highlights: list[dict]) -> str:
    if not highlights:
        return "No highlights detected for this stream."
    total = len(highlights)
    peak = max(highlights, key=lambda h: h["intensity"])
    categories: dict[str, int] = {}
    for h in highlights:
        cat = h.get("category", "hype")
        categories[cat] = categories.get(cat, 0) + 1

    parts = [f"{total} highlight moment{'s' if total > 1 else ''} detected."]
    parts.append(f"Peak moment: {peak['description']} (intensity: {peak['intensity']:.0f}/100).")
    cat_parts = [f"{count} {cat}" for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)]
    parts.append(f"Categories: {', '.join(cat_parts)}.")
    return " ".join(parts)


async def delete_highlight(highlight_id: str) -> bool:
    async with get_conn() as conn:
        cur = await conn.execute(
            "DELETE FROM highlight_markers WHERE id = %s", (highlight_id,),
        )
        await conn.commit()
        return cur.rowcount > 0
