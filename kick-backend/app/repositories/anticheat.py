"""Repository for anti-cheat data access (raids, fraud)."""

from typing import Optional

from app.services.db import get_conn, _now_iso


async def list_raids(channel: Optional[str] = None, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM raid_events WHERE channel = %s ORDER BY detected_at DESC LIMIT %s",
                (channel, limit),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM raid_events ORDER BY detected_at DESC LIMIT %s",
                (limit,),
            )
        return [dict(r) for r in await row.fetchall()]


async def get_raid(raid_id: int) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM raid_events WHERE id = %s",
            (raid_id,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def resolve_raid(raid_id: int) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE raid_events SET resolved = TRUE, resolved_at = %s
               WHERE id = %s RETURNING *""",
            (_now_iso(), raid_id),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_fraud_flags(giveaway_id: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM giveaway_fraud_flags WHERE giveaway_id = %s ORDER BY confidence DESC",
            (giveaway_id,),
        )
        return [dict(r) for r in await row.fetchall()]


async def review_fraud_flag(flag_id: int, action: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE giveaway_fraud_flags SET reviewed = TRUE, review_action = %s
               WHERE id = %s RETURNING *""",
            (action, flag_id),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_raid_settings() -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM raid_settings WHERE id = 1")
        result = await row.fetchone()
    if result:
        d = dict(result)
        d.pop("id", None)
        return d
    return {
        "enabled": True,
        "new_chatter_threshold": 20,
        "window_seconds": 60,
        "auto_action": "none",
        "min_account_age_days": 7,
    }


async def upsert_raid_settings(
    enabled: bool,
    new_chatter_threshold: int,
    window_seconds: int,
    auto_action: str,
    min_account_age_days: int,
) -> dict:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO raid_settings (id, enabled, new_chatter_threshold, window_seconds, auto_action, min_account_age_days)
               VALUES (1, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
                   enabled = EXCLUDED.enabled,
                   new_chatter_threshold = EXCLUDED.new_chatter_threshold,
                   window_seconds = EXCLUDED.window_seconds,
                   auto_action = EXCLUDED.auto_action,
                   min_account_age_days = EXCLUDED.min_account_age_days""",
            (enabled, new_chatter_threshold, window_seconds, auto_action, min_account_age_days),
        )
        await conn.commit()
    return {
        "enabled": enabled,
        "new_chatter_threshold": new_chatter_threshold,
        "window_seconds": window_seconds,
        "auto_action": auto_action,
        "min_account_age_days": min_account_age_days,
    }
