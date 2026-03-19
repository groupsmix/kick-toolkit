"""Repository for Discord Bot Integration data access."""

from app.services.db import get_conn, _generate_id, _now_iso


async def get_config(channel: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM discord_bot_configs WHERE channel = %s", (channel,),
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def upsert_config(channel: str, **kwargs) -> dict:
    now = _now_iso()
    existing = await get_config(channel)
    if existing:
        updates = []
        params: list = []
        for key, value in kwargs.items():
            if value is not None and key in (
                "guild_id", "webhook_url", "go_live_enabled", "go_live_channel_id",
                "go_live_message", "chat_bridge_enabled", "chat_bridge_channel_id",
                "sub_sync_enabled", "sub_sync_role_id", "stats_commands_enabled",
                "schedule_display_enabled", "schedule_channel_id",
            ):
                updates.append(f"{key} = %s")
                params.append(value)
        updates.append("updated_at = %s")
        params.append(now)
        params.append(channel)
        async with get_conn() as conn:
            await conn.execute(
                f"UPDATE discord_bot_configs SET {', '.join(updates)} WHERE channel = %s",
                tuple(params),
            )
            await conn.commit()
        return (await get_config(channel)) or {}
    else:
        config_id = _generate_id()
        guild_id = kwargs.get("guild_id", "")
        webhook_url = kwargs.get("webhook_url", "")
        go_live_enabled = kwargs.get("go_live_enabled", True)
        go_live_channel_id = kwargs.get("go_live_channel_id", "")
        go_live_message = kwargs.get("go_live_message",
                                     "{streamer} is now live on Kick! Playing {game} - {title}")
        chat_bridge_enabled = kwargs.get("chat_bridge_enabled", False)
        chat_bridge_channel_id = kwargs.get("chat_bridge_channel_id", "")
        sub_sync_enabled = kwargs.get("sub_sync_enabled", False)
        sub_sync_role_id = kwargs.get("sub_sync_role_id", "")
        stats_commands_enabled = kwargs.get("stats_commands_enabled", True)
        schedule_display_enabled = kwargs.get("schedule_display_enabled", True)
        schedule_channel_id = kwargs.get("schedule_channel_id", "")

        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO discord_bot_configs
                   (id, channel, guild_id, webhook_url, go_live_enabled, go_live_channel_id,
                    go_live_message, chat_bridge_enabled, chat_bridge_channel_id,
                    sub_sync_enabled, sub_sync_role_id, stats_commands_enabled,
                    schedule_display_enabled, schedule_channel_id, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (config_id, channel, guild_id, webhook_url, go_live_enabled,
                 go_live_channel_id, go_live_message, chat_bridge_enabled,
                 chat_bridge_channel_id, sub_sync_enabled, sub_sync_role_id,
                 stats_commands_enabled, schedule_display_enabled, schedule_channel_id, now),
            )
            await conn.commit()
        return (await get_config(channel)) or {}


async def get_status(channel: str) -> dict:
    config = await get_config(channel)
    if not config:
        return {
            "channel": channel, "connected": False,
            "guild_name": "", "features_active": [], "last_ping": None,
        }
    features = []
    if config.get("go_live_enabled"):
        features.append("go_live")
    if config.get("chat_bridge_enabled"):
        features.append("chat_bridge")
    if config.get("sub_sync_enabled"):
        features.append("sub_sync")
    if config.get("stats_commands_enabled"):
        features.append("stats_commands")
    if config.get("schedule_display_enabled"):
        features.append("schedule_display")
    return {
        "channel": channel,
        "connected": bool(config.get("guild_id")),
        "guild_name": f"Guild {config.get('guild_id', '')[:6]}..." if config.get("guild_id") else "",
        "features_active": features,
        "last_ping": config.get("updated_at"),
    }
