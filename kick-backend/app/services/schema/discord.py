"""Discord Bot Integration schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS discord_bot_configs (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL UNIQUE,
    guild_id TEXT NOT NULL DEFAULT '',
    webhook_url TEXT NOT NULL DEFAULT '',
    go_live_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    go_live_channel_id TEXT NOT NULL DEFAULT '',
    go_live_message TEXT NOT NULL DEFAULT '{streamer} is now live on Kick! Playing {game} - {title}',
    chat_bridge_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    chat_bridge_channel_id TEXT NOT NULL DEFAULT '',
    sub_sync_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sub_sync_role_id TEXT NOT NULL DEFAULT '',
    stats_commands_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    schedule_display_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    schedule_channel_id TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""
