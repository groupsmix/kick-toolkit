"""Repository for whitelisted users data access."""

from app.services.db import get_conn, _now_iso


async def list_whitelisted(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM whitelisted_users WHERE channel = %s ORDER BY created_at DESC",
            (channel,),
        )
        return [dict(r) for r in await row.fetchall()]


async def add_whitelisted(
    username: str,
    channel: str,
    added_by: str = "",
    reason: str = "",
    tier: str = "regular",
    auto_whitelisted: bool = False,
    message_count: int = 0,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO whitelisted_users
               (username, channel, added_by, reason, tier, auto_whitelisted, message_count_at_whitelist, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (username, channel) DO UPDATE SET
                   tier = EXCLUDED.tier, reason = EXCLUDED.reason""",
            (username, channel, added_by, reason, tier, auto_whitelisted, message_count, now),
        )
        # Also remove from flagged accounts
        await conn.execute(
            "DELETE FROM flagged_accounts WHERE lower(username) = lower(%s)",
            (username,),
        )
        await conn.commit()
    return {
        "username": username, "channel": channel, "added_by": added_by,
        "reason": reason, "tier": tier, "auto_whitelisted": auto_whitelisted,
        "message_count_at_whitelist": message_count, "created_at": now,
    }


async def remove_whitelisted(username: str, channel: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM whitelisted_users WHERE lower(username) = lower(%s) AND channel = %s",
            (username, channel),
        )
        await conn.commit()


async def is_whitelisted(username: str, channel: str) -> bool:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT 1 FROM whitelisted_users WHERE lower(username) = lower(%s) AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return result is not None
