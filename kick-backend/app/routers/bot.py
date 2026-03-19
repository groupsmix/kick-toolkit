"""Bot configuration and commands router."""

import logging
import random

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import BotConfig, BotCommand, ModerationRule, ChatMessage, ModerationResult
from app.repositories import bot as bot_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.get("/config/{channel}")
async def get_bot_config(channel: str, _session: dict = Depends(require_auth)) -> dict:
    config = await bot_repo.get_config(channel)
    if config:
        return dict(config)
    return {"channel": channel, "prefix": "!", "enabled": False, "welcome_message": None, "auto_mod_enabled": False}


@router.post("/config")
async def set_bot_config(config: BotConfig, _session: dict = Depends(require_auth)) -> dict:
    await bot_repo.upsert_config(
        config.channel, config.prefix, config.enabled,
        config.welcome_message, config.auto_mod_enabled,
    )
    logger.info("Bot config updated for channel=%s", config.channel)
    return config.model_dump()


@router.get("/commands/{channel}")
async def get_commands(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await bot_repo.list_commands(channel)


@router.post("/commands/{channel}")
async def add_command(channel: str, command: BotCommand, _session: dict = Depends(require_auth)) -> dict:
    await bot_repo.create_command(
        channel, command.name, command.response,
        command.cooldown, command.enabled, command.mod_only,
    )
    logger.info("Command !%s added for channel=%s", command.name, channel)
    return command.model_dump()


@router.delete("/commands/{channel}/{command_name}")
async def delete_command(channel: str, command_name: str, _session: dict = Depends(require_auth)) -> dict:
    await bot_repo.delete_command(channel, command_name)
    logger.info("Command !%s deleted from channel=%s", command_name, channel)
    return {"status": "deleted"}


@router.put("/commands/{channel}/{command_name}")
async def update_command(channel: str, command_name: str, command: BotCommand, _session: dict = Depends(require_auth)) -> dict:
    updated = await bot_repo.update_command(
        channel, command_name, command.name, command.response,
        command.cooldown, command.enabled, command.mod_only,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Command not found")
    logger.info("Command !%s updated in channel=%s", command_name, channel)
    return updated


# ========== Moderation ==========
mod_router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@mod_router.get("/rules/{channel}")
async def get_moderation_rules(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await bot_repo.list_moderation_rules(channel)


@mod_router.post("/rules/{channel}")
async def add_moderation_rule(channel: str, rule: ModerationRule, _session: dict = Depends(require_auth)) -> dict:
    rule_id = await bot_repo.create_moderation_rule(
        channel, rule.name, rule.type, rule.enabled,
        rule.action, rule.severity, rule.settings,
    )
    logger.info("Moderation rule '%s' created for channel=%s", rule.name, channel)
    result = rule.model_dump()
    result["id"] = rule_id
    return result


@mod_router.put("/rules/{channel}/{rule_id}")
async def update_moderation_rule(channel: str, rule_id: str, rule: ModerationRule, _session: dict = Depends(require_auth)) -> dict:
    updated = await bot_repo.update_moderation_rule(
        channel, rule_id, rule.name, rule.type, rule.enabled,
        rule.action, rule.severity, rule.settings,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    logger.info("Moderation rule '%s' updated in channel=%s", rule.name, channel)
    return updated


@mod_router.delete("/rules/{channel}/{rule_id}")
async def delete_moderation_rule(channel: str, rule_id: str, _session: dict = Depends(require_auth)) -> dict:
    await bot_repo.delete_moderation_rule(channel, rule_id)
    logger.info("Moderation rule %s deleted from channel=%s", rule_id, channel)
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
