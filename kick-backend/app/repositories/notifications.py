"""Repository for go-live notification settings and history."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_notification_settings(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM notification_settings WHERE channel = %s", (channel,),
        )
        result = await row.fetchone()
    if result:
        d = dict(result)
        if isinstance(d.get("webhook_urls"), str):
            d["webhook_urls"] = json.loads(d["webhook_urls"])
        return d
    return None


async def upsert_notification_settings(
    channel: str,
    go_live_enabled: bool,
    webhook_urls: list[str],
    discord_webhook_url: str,
    notification_message: str,
    notify_on_title_change: bool,
    notify_on_game_change: bool,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO notification_settings
               (channel, go_live_enabled, webhook_urls, discord_webhook_url,
                notification_message, notify_on_title_change, notify_on_game_change, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   go_live_enabled = EXCLUDED.go_live_enabled,
                   webhook_urls = EXCLUDED.webhook_urls,
                   discord_webhook_url = EXCLUDED.discord_webhook_url,
                   notification_message = EXCLUDED.notification_message,
                   notify_on_title_change = EXCLUDED.notify_on_title_change,
                   notify_on_game_change = EXCLUDED.notify_on_game_change,
                   updated_at = EXCLUDED.updated_at""",
            (channel, go_live_enabled, json.dumps(webhook_urls), discord_webhook_url,
             notification_message, notify_on_title_change, notify_on_game_change, now),
        )
        await conn.commit()
    return {
        "channel": channel, "go_live_enabled": go_live_enabled,
        "webhook_urls": webhook_urls, "discord_webhook_url": discord_webhook_url,
        "notification_message": notification_message,
        "notify_on_title_change": notify_on_title_change,
        "notify_on_game_change": notify_on_game_change,
        "updated_at": now,
    }


async def log_notification(
    channel: str, notification_type: str, message: str, targets: list[str],
) -> dict:
    nid = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO notification_log
               (id, channel, notification_type, message, targets, status, created_at)
               VALUES (%s, %s, %s, %s, %s, 'sent', %s)""",
            (nid, channel, notification_type, message, json.dumps(targets), now),
        )
        await conn.commit()
    return {
        "id": nid, "channel": channel, "notification_type": notification_type,
        "message": message, "targets": targets, "status": "sent", "created_at": now,
    }


async def get_notification_history(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM notification_log WHERE channel = %s
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    parsed = []
    for r in results:
        d = dict(r)
        if isinstance(d.get("targets"), str):
            d["targets"] = json.loads(d["targets"])
        parsed.append(d)
    return parsed
