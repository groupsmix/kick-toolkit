"""Bot configuration and commands router."""

import json
import random

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import BotConfig, BotCommand, ModerationRule, ChatMessage, ModerationResult
from app.services.db import get_conn, _generate_id

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.get("/config/{channel}")
async def get_bot_config(channel: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM bot_configs WHERE channel = %s", (channel,))
        config = await row.fetchone()
    if config:
        return dict(config)
    return {"channel": channel, "prefix": "!", "enabled": False, "welcome_message": None, "auto_mod_enabled": False}


@router.post("/config")
async def set_bot_config(config: BotConfig, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bot_configs (channel, prefix, enabled, welcome_message, auto_mod_enabled)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   prefix = EXCLUDED.prefix, enabled = EXCLUDED.enabled,
                   welcome_message = EXCLUDED.welcome_message, auto_mod_enabled = EXCLUDED.auto_mod_enabled""",
            (config.channel, config.prefix, config.enabled, config.welcome_message, config.auto_mod_enabled),
        )
        await conn.commit()
    return config.model_dump()


@router.get("/commands/{channel}")
async def get_commands(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT name, response, cooldown, enabled, mod_only FROM bot_commands WHERE channel = %s",
            (channel,),
        )
        commands = await row.fetchall()
    return [dict(c) for c in commands]


@router.post("/commands/{channel}")
async def add_command(channel: str, command: BotCommand, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO bot_commands (channel, name, response, cooldown, enabled, mod_only)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (channel, command.name, command.response, command.cooldown, command.enabled, command.mod_only),
        )
        await conn.commit()
    return command.model_dump()


@router.delete("/commands/{channel}/{command_name}")
async def delete_command(channel: str, command_name: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM bot_commands WHERE channel = %s AND name = %s",
            (channel, command_name),
        )
        await conn.commit()
    return {"status": "deleted"}


@router.put("/commands/{channel}/{command_name}")
async def update_command(channel: str, command_name: str, command: BotCommand, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE bot_commands SET name = %s, response = %s, cooldown = %s, enabled = %s, mod_only = %s
               WHERE channel = %s AND name = %s RETURNING name, response, cooldown, enabled, mod_only""",
            (command.name, command.response, command.cooldown, command.enabled, command.mod_only, channel, command_name),
        )
        updated = await row.fetchone()
        await conn.commit()
    if not updated:
        raise HTTPException(status_code=404, detail="Command not found")
    return dict(updated)


# ========== Moderation ==========
mod_router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@mod_router.get("/rules/{channel}")
async def get_moderation_rules(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM moderation_rules WHERE channel = %s", (channel,))
        rules = await row.fetchall()
    return [dict(r) for r in rules]


@mod_router.post("/rules/{channel}")
async def add_moderation_rule(channel: str, rule: ModerationRule, _session: dict = Depends(require_auth)) -> dict:
    rule_id = _generate_id()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO moderation_rules (id, channel, name, type, enabled, action, severity, settings)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (rule_id, channel, rule.name, rule.type, rule.enabled, rule.action, rule.severity, json.dumps(rule.settings)),
        )
        await conn.commit()
    result = rule.model_dump()
    result["id"] = rule_id
    return result


@mod_router.put("/rules/{channel}/{rule_id}")
async def update_moderation_rule(channel: str, rule_id: str, rule: ModerationRule, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE moderation_rules SET name = %s, type = %s, enabled = %s, action = %s, severity = %s, settings = %s
               WHERE id = %s AND channel = %s RETURNING *""",
            (rule.name, rule.type, rule.enabled, rule.action, rule.severity, json.dumps(rule.settings), rule_id, channel),
        )
        updated = await row.fetchone()
        await conn.commit()
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    return dict(updated)


@mod_router.delete("/rules/{channel}/{rule_id}")
async def delete_moderation_rule(channel: str, rule_id: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM moderation_rules WHERE id = %s AND channel = %s", (rule_id, channel))
        await conn.commit()
    return {"status": "deleted"}


@mod_router.post("/analyze")
async def analyze_message(msg: ChatMessage) -> ModerationResult:
    """Simulate AI moderation analysis of a chat message."""
    text = msg.message.lower()
    flagged = False
    reason = None
    action = None
    confidence = 0.0

    toxic_patterns = ["trash", "garbage", "stupid", "idiot", "kill", "die", "hate", "suck", "worst"]
    spam_patterns = ["bit.ly", "free viewers", "follow me", "buy followers", "check out my"]

    toxic_count = sum(1 for p in toxic_patterns if p in text)
    if toxic_count > 0:
        confidence = min(0.5 + toxic_count * 0.15, 0.98)
        if confidence > 0.6:
            flagged = True
            reason = f"AI: Toxicity detected ({confidence:.2f})"
            action = "delete"

    spam_count = sum(1 for p in spam_patterns if p in text)
    if spam_count > 0:
        confidence = min(0.7 + spam_count * 0.1, 0.99)
        flagged = True
        reason = "Link spam detected"
        action = "delete"

    if len(msg.message) > 10:
        caps_ratio = sum(1 for c in msg.message if c.isupper()) / len(msg.message)
        if caps_ratio > 0.7:
            flagged = True
            confidence = caps_ratio
            reason = f"Excessive caps ({int(caps_ratio * 100)}%)"
            action = "warn"

    if any(c * 8 in text for c in "abcdefghijklmnopqrstuvwxyz!?"):
        flagged = True
        confidence = 0.85
        reason = "Spam: Repeated characters"
        action = "delete"

    return ModerationResult(flagged=flagged, reason=reason, action=action, confidence=confidence)
