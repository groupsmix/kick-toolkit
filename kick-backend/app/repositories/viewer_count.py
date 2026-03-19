"""Repository for viewer count tracker."""

from app.services.db import get_conn, _now_iso


async def record_snapshot(channel: str, viewer_count: int) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "INSERT INTO viewer_count_snapshots (channel, viewer_count, recorded_at) VALUES (%s, %s, %s)",
            (channel, viewer_count, now),
        )
        await conn.commit()
    return {"channel": channel, "viewer_count": viewer_count, "recorded_at": now}


async def get_history(channel: str, limit: int = 100) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT viewer_count, recorded_at FROM viewer_count_snapshots
               WHERE channel = %s ORDER BY recorded_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_stats(channel: str) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT COUNT(*) as total_snapshots,
                      COALESCE(MAX(viewer_count), 0) as peak_viewers,
                      COALESCE(AVG(viewer_count), 0) as avg_viewers,
                      COALESCE(MIN(viewer_count), 0) as min_viewers
               FROM viewer_count_snapshots WHERE channel = %s""",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else {
        "total_snapshots": 0, "peak_viewers": 0, "avg_viewers": 0, "min_viewers": 0,
    }
