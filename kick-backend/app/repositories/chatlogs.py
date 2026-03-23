"""Repository for chat logs data access."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def query_logs(
    channel: Optional[str] = None,
    username: Optional[str] = None,
    flagged_only: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    conditions: list[str] = []
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
        conditions.append("(lower(message) LIKE %s ESCAPE '\\' OR lower(username) LIKE %s ESCAPE '\\')")
        escaped = search.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        params.extend([pattern, pattern])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_conn() as conn:
        row = await conn.execute(f"SELECT count(*) AS cnt FROM chat_logs {where}", params)
        total = (await row.fetchone())["cnt"]

        row = await conn.execute(
            f"SELECT * FROM chat_logs {where} ORDER BY timestamp LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        logs = [dict(r) for r in await row.fetchall()]

    return logs, total


async def get_user_logs(username: str) -> dict:
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


async def insert_log(channel: str, username: str, message: str, timestamp: Optional[str], flagged: bool, flag_reason: Optional[str]) -> dict:
    log_id = _generate_id()
    ts = timestamp or _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO chat_logs (id, channel, username, message, timestamp, flagged, flag_reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (log_id, channel, username, message, ts, flagged, flag_reason),
        )
        await conn.commit()
    return {
        "id": log_id, "channel": channel, "username": username,
        "message": message, "timestamp": ts,
        "flagged": flagged, "flag_reason": flag_reason,
    }


async def get_stats(channel: str) -> dict:
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
