"""Repository for banned users data access."""

from app.services.db import get_conn, _now_iso


async def list_banned(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM banned_users WHERE channel = %s ORDER BY banned_at DESC",
            (channel,),
        )
        return [dict(r) for r in await row.fetchall()]


async def add_banned(
    username: str,
    channel: str,
    ban_reason: str = "",
    ban_source: str = "manual",
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO banned_users (username, channel, banned_at, ban_reason, ban_source)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (username, channel) DO UPDATE SET
                   ban_reason = EXCLUDED.ban_reason, ban_source = EXCLUDED.ban_source""",
            (username, channel, now, ban_reason, ban_source),
        )
        await conn.commit()
    return {
        "username": username, "channel": channel,
        "banned_at": now, "ban_reason": ban_reason, "ban_source": ban_source,
    }


async def remove_banned(username: str, channel: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM banned_users WHERE lower(username) = lower(%s) AND channel = %s",
            (username, channel),
        )
        await conn.commit()


async def get_banned_usernames(channel: str) -> list[str]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT username FROM banned_users WHERE channel = %s",
            (channel,),
        )
        return [r["username"] for r in await row.fetchall()]
