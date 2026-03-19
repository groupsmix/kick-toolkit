"""Repository for Discord bot integration — settings, webhook events."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Discord Settings
# ---------------------------------------------------------------------------

async def get_settings(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM discord_settings WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_settings(channel: str, **kwargs: object) -> dict:
    now = _now_iso()
    existing = await get_settings(channel)

    if existing:
        if not kwargs:
            return existing
        set_parts = []
        values: list[object] = []
        for key, val in kwargs.items():
            set_parts.append(f"{key} = %s")
            values.append(val)
        set_parts.append("updated_at = %s")
        values.append(now)
        values.append(channel)
        async with get_conn() as conn:
            await conn.execute(
                f"UPDATE discord_settings SET {', '.join(set_parts)} WHERE channel = %s",
                tuple(values),
            )
            await conn.commit()
    else:
        defaults = {
            "enabled": True,
            "guild_id": "",
            "webhook_url": "",
            "go_live_notifications": True,
            "go_live_channel_id": "",
            "go_live_message": "🔴 {streamer} is now live on Kick! Playing {game}\n{url}",
            "chat_bridge_enabled": False,
            "chat_bridge_channel_id": "",
            "sub_sync_enabled": False,
            "sub_sync_role_id": "",
            "stats_command_enabled": True,
            "schedule_command_enabled": True,
        }
        defaults.update(kwargs)
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO discord_settings
                   (channel, enabled, guild_id, webhook_url,
                    go_live_notifications, go_live_channel_id, go_live_message,
                    chat_bridge_enabled, chat_bridge_channel_id,
                    sub_sync_enabled, sub_sync_role_id,
                    stats_command_enabled, schedule_command_enabled, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (channel, defaults["enabled"], defaults["guild_id"], defaults["webhook_url"],
                 defaults["go_live_notifications"], defaults["go_live_channel_id"],
                 defaults["go_live_message"], defaults["chat_bridge_enabled"],
                 defaults["chat_bridge_channel_id"], defaults["sub_sync_enabled"],
                 defaults["sub_sync_role_id"], defaults["stats_command_enabled"],
                 defaults["schedule_command_enabled"], now),
            )
            await conn.commit()

    result = await get_settings(channel)
    return result or {"channel": channel, "updated_at": now}


# ---------------------------------------------------------------------------
# Webhook Events
# ---------------------------------------------------------------------------

async def create_event(
    channel: str, event_type: str, payload: dict,
) -> dict:
    event_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO discord_webhook_events
               (id, channel, event_type, payload, status, created_at)
               VALUES (%s, %s, %s, %s, 'pending', %s)""",
            (event_id, channel, event_type, json.dumps(payload), now),
        )
        await conn.commit()
    return {
        "id": event_id, "channel": channel, "event_type": event_type,
        "payload": payload, "status": "pending", "error": None, "created_at": now,
    }


async def update_event_status(event_id: str, status: str, error: Optional[str] = None) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE discord_webhook_events SET status = %s, error = %s WHERE id = %s",
            (status, error, event_id),
        )
        await conn.commit()


async def list_events(channel: str, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM discord_webhook_events WHERE channel = %s
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    out = []
    for r in results:
        d = dict(r)
        if isinstance(d.get("payload"), str):
            d["payload"] = json.loads(d["payload"])
        out.append(d)
    return out


async def get_event(event_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM discord_webhook_events WHERE id = %s", (event_id,)
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        if isinstance(d.get("payload"), str):
            d["payload"] = json.loads(d["payload"])
        return d
    return None
