"""Activity / audit log API routes."""

import json

from fastapi import APIRouter, Depends

from app.dependencies import require_auth
from app.services.db import get_conn, _now_iso, _generate_id

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("")
async def get_activity_log(
    limit: int = 50,
    session: dict = Depends(require_auth),
):
    """Return the recent activity log entries for the authenticated user."""
    user_data = session.get("user_data")
    if isinstance(user_data, str):
        user_data = json.loads(user_data)
    channel = user_data.get("streamer_channel") or user_data.get("name", "") if user_data else ""

    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM activity_log
               WHERE channel = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (channel, min(limit, 200)),
        )
        rows = await row.fetchall()
    return {"entries": [dict(r) for r in rows]}


@router.post("")
async def create_activity(
    action: str,
    detail: str = "",
    session: dict = Depends(require_auth),
):
    """Create an activity log entry."""
    user_data = session.get("user_data")
    if isinstance(user_data, str):
        user_data = json.loads(user_data)
    channel = user_data.get("streamer_channel") or user_data.get("name", "") if user_data else ""

    entry_id = _generate_id()
    now = _now_iso()

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO activity_log (id, channel, action, detail, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (entry_id, channel, action, detail, now),
        )
        await conn.commit()

    return {"id": entry_id, "channel": channel, "action": action, "detail": detail, "created_at": now}
