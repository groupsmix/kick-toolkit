"""Repository for bot configuration, commands, and moderation rules."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id


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
) -> None:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bot_configs (channel, prefix, enabled, welcome_message, auto_mod_enabled)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   prefix = EXCLUDED.prefix, enabled = EXCLUDED.enabled,
                   welcome_message = EXCLUDED.welcome_message, auto_mod_enabled = EXCLUDED.auto_mod_enabled""",
            (channel, prefix, enabled, welcome_message, auto_mod_enabled),
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
