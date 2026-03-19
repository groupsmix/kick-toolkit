"""Chat logs router."""

from fastapi import APIRouter, Query, Depends
from typing import Optional

from app.dependencies import require_auth
from app.services.db import get_conn, _generate_id, _now_iso

router = APIRouter(prefix="/api/chatlogs", tags=["chatlogs"])


@router.get("")
async def get_chat_logs(
    channel: Optional[str] = None,
    username: Optional[str] = None,
    flagged_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    _session: dict = Depends(require_auth),
) -> dict:
    conditions = []
    params: list = []

    if channel:
        conditions.append("channel = %s")
        params.append(channel)
    if username:
        conditions.append("lower(username) = lower(%s)")
        params.append(username)
    if flagged_only:
        conditions.append("flagged = TRUE")
    if search:
        conditions.append("(lower(message) LIKE %s OR lower(username) LIKE %s)")
        pattern = f"%{search.lower()}%"
        params.extend([pattern, pattern])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_conn() as conn:
        row = await conn.execute(f"SELECT count(*) AS cnt FROM chat_logs {where}", params)
        total = (await row.fetchone())["cnt"]

        row = await conn.execute(
            f"SELECT * FROM chat_logs {where} ORDER BY timestamp LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        logs = await row.fetchall()

    return {"logs": [dict(l) for l in logs], "total": total, "limit": limit, "offset": offset}


@router.get("/user/{username}")
async def get_user_logs(username: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM chat_logs WHERE lower(username) = lower(%s) ORDER BY timestamp DESC LIMIT 100",
            (username,),
        )
        user_logs = [dict(r) for r in await row.fetchall()]

        row = await conn.execute(
            "SELECT count(*) AS cnt FROM chat_logs WHERE lower(username) = lower(%s)",
            (username,),
        )
        total_messages = (await row.fetchone())["cnt"]

        row = await conn.execute(
            "SELECT count(*) AS cnt FROM chat_logs WHERE lower(username) = lower(%s) AND flagged = TRUE",
            (username,),
        )
        flagged_messages = (await row.fetchone())["cnt"]

        row = await conn.execute(
            "SELECT DISTINCT channel FROM chat_logs WHERE lower(username) = lower(%s)",
            (username,),
        )
        channels = [r["channel"] for r in await row.fetchall()]

    return {
        "username": username,
        "total_messages": total_messages,
        "flagged_messages": flagged_messages,
        "channels": channels,
        "logs": user_logs,
    }


@router.post("")
async def add_chat_log(entry: dict, _session: dict = Depends(require_auth)) -> dict:
    log_id = _generate_id()
    timestamp = entry.get("timestamp") or _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO chat_logs (id, channel, username, message, timestamp, flagged, flag_reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (log_id, entry["channel"], entry["username"], entry["message"],
             timestamp, entry.get("flagged", False), entry.get("flag_reason")),
        )
        await conn.commit()
    return {
        "id": log_id, "channel": entry["channel"], "username": entry["username"],
        "message": entry["message"], "timestamp": timestamp,
        "flagged": entry.get("flagged", False), "flag_reason": entry.get("flag_reason"),
    }


@router.get("/stats/{channel}")
async def get_chat_stats(channel: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs WHERE channel = %s", (channel,))
        total = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs WHERE channel = %s AND flagged = TRUE", (channel,))
        flagged = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(DISTINCT username) AS cnt FROM chat_logs WHERE channel = %s", (channel,))
        unique_users = (await row.fetchone())["cnt"]

        row = await conn.execute(
            "SELECT username, count(*) AS cnt FROM chat_logs WHERE channel = %s GROUP BY username ORDER BY cnt DESC LIMIT 10",
            (channel,),
        )
        top_chatters = [{"username": r["username"], "count": r["cnt"]} for r in await row.fetchall()]

    return {
        "channel": channel,
        "total_messages": total,
        "flagged_messages": flagged,
        "unique_users": unique_users,
        "top_chatters": top_chatters,
    }
