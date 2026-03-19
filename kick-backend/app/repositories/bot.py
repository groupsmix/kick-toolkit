"""Repository for bot configuration, commands, moderation rules, timed messages, and shoutout config."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_config(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM bot_configs WHERE channel = %s", (channel,)
        )
        config = await row.fetchone()
    return dict(config) if config else None


async def upsert_config(
    channel: str,
    prefix: str,
    enabled: bool,
    welcome_message: Optional[str],
    auto_mod_enabled: bool,
    welcome_enabled: bool = False,
    welcome_new_message: Optional[str] = None,
    welcome_returning_message: Optional[str] = None,
    welcome_subscriber_message: Optional[str] = None,
    shoutout_template: str = "Check out {target} at kick.com/{target}! They were last playing {game}.",
    auto_shoutout_raiders: bool = False,
) -> None:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bot_configs (channel, prefix, enabled, welcome_message, auto_mod_enabled,
                   welcome_enabled, welcome_new_message, welcome_returning_message,
                   welcome_subscriber_message, shoutout_template, auto_shoutout_raiders)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   prefix = EXCLUDED.prefix, enabled = EXCLUDED.enabled,
                   welcome_message = EXCLUDED.welcome_message, auto_mod_enabled = EXCLUDED.auto_mod_enabled,
                   welcome_enabled = EXCLUDED.welcome_enabled,
                   welcome_new_message = EXCLUDED.welcome_new_message,
                   welcome_returning_message = EXCLUDED.welcome_returning_message,
                   welcome_subscriber_message = EXCLUDED.welcome_subscriber_message,
                   shoutout_template = EXCLUDED.shoutout_template,
                   auto_shoutout_raiders = EXCLUDED.auto_shoutout_raiders""",
            (channel, prefix, enabled, welcome_message, auto_mod_enabled,
             welcome_enabled, welcome_new_message, welcome_returning_message,
             welcome_subscriber_message, shoutout_template, auto_shoutout_raiders),
        )
        await conn.commit()


async def list_commands(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT name, response, cooldown, enabled, mod_only FROM bot_commands WHERE channel = %s",
            (channel,),
        )
        commands = await row.fetchall()
    return [dict(c) for c in commands]


async def create_command(
    channel: str,
    name: str,
    response: str,
    cooldown: int,
    enabled: bool,
    mod_only: bool,
) -> None:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bot_commands (channel, name, response, cooldown, enabled, mod_only)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (channel, name, response, cooldown, enabled, mod_only),
        )
        await conn.commit()


async def delete_command(channel: str, command_name: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM bot_commands WHERE channel = %s AND name = %s",
            (channel, command_name),
        )
        await conn.commit()


async def update_command(
    channel: str,
    old_name: str,
    name: str,
    response: str,
    cooldown: int,
    enabled: bool,
    mod_only: bool,
) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE bot_commands SET name = %s, response = %s, cooldown = %s, enabled = %s, mod_only = %s
               WHERE channel = %s AND name = %s RETURNING name, response, cooldown, enabled, mod_only""",
            (name, response, cooldown, enabled, mod_only, channel, old_name),
        )
        updated = await row.fetchone()
        await conn.commit()
    return dict(updated) if updated else None


async def list_moderation_rules(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM moderation_rules WHERE channel = %s", (channel,)
        )
        rules = await row.fetchall()
    return [dict(r) for r in rules]


async def create_moderation_rule(
    channel: str,
    name: str,
    rule_type: str,
    enabled: bool,
    action: str,
    severity: int,
    settings: dict,
) -> str:
    rule_id = _generate_id()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO moderation_rules (id, channel, name, type, enabled, action, severity, settings)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (rule_id, channel, name, rule_type, enabled, action, severity, json.dumps(settings)),
        )
        await conn.commit()
    return rule_id


async def update_moderation_rule(
    channel: str,
    rule_id: str,
    name: str,
    rule_type: str,
    enabled: bool,
    action: str,
    severity: int,
    settings: dict,
) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE moderation_rules SET name = %s, type = %s, enabled = %s, action = %s, severity = %s, settings = %s
               WHERE id = %s AND channel = %s RETURNING *""",
            (name, rule_type, enabled, action, severity, json.dumps(settings), rule_id, channel),
        )
        updated = await row.fetchone()
        await conn.commit()
    return dict(updated) if updated else None


async def delete_moderation_rule(channel: str, rule_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM moderation_rules WHERE id = %s AND channel = %s",
            (rule_id, channel),
        )
        await conn.commit()


# ========== Timed Messages ==========

async def list_timed_messages(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM timed_messages WHERE channel = %s ORDER BY created_at",
            (channel,),
        )
        messages = await row.fetchall()
    return [dict(m) for m in messages]


async def create_timed_message(
    channel: str,
    message: str,
    interval_minutes: int,
    enabled: bool,
) -> str:
    msg_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO timed_messages (id, channel, message, interval_minutes, enabled, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (msg_id, channel, message, interval_minutes, enabled, now),
        )
        await conn.commit()
    return msg_id


async def update_timed_message(
    channel: str,
    msg_id: str,
    message: Optional[str] = None,
    interval_minutes: Optional[int] = None,
    enabled: Optional[bool] = None,
) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM timed_messages WHERE id = %s AND channel = %s",
            (msg_id, channel),
        )
        existing = await row.fetchone()
        if not existing:
            return None
        existing = dict(existing)

        new_message = message if message is not None else existing["message"]
        new_interval = interval_minutes if interval_minutes is not None else existing["interval_minutes"]
        new_enabled = enabled if enabled is not None else existing["enabled"]

        row = await conn.execute(
            """UPDATE timed_messages SET message = %s, interval_minutes = %s, enabled = %s
               WHERE id = %s AND channel = %s RETURNING *""",
            (new_message, new_interval, new_enabled, msg_id, channel),
        )
        updated = await row.fetchone()
        await conn.commit()
    return dict(updated) if updated else None


async def delete_timed_message(channel: str, msg_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM timed_messages WHERE id = %s AND channel = %s",
            (msg_id, channel),
        )
        await conn.commit()


# ========== Welcome Check ==========

async def check_welcome_type(channel: str, username: str) -> str:
    """Determine welcome type for a user: 'new', 'returning', 'subscriber', or 'none'."""
    async with get_conn() as conn:
        # Check viewer_profiles table for user history
        row = await conn.execute(
            "SELECT * FROM viewer_profiles WHERE channel = %s AND username = %s",
            (channel, username),
        )
        profile = await row.fetchone()

        if not profile:
            # Also check chat_logs for any previous messages
            row = await conn.execute(
                "SELECT count(*) AS cnt FROM chat_logs WHERE channel = %s AND username = %s",
                (channel, username),
            )
            log_result = await row.fetchone()
            if log_result and log_result["cnt"] > 0:
                return "returning"
            return "new"

        profile = dict(profile)
        if profile.get("is_subscriber"):
            return "subscriber"
        return "returning"
