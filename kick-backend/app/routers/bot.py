"""Bot configuration and commands router."""

from fastapi import APIRouter
from app.models.schemas import BotConfig, BotCommand, ModerationRule, ChatMessage, ModerationResult
from app.services.database import bot_configs, bot_commands, moderation_rules, generate_id
import random

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.get("/config/{channel}")
async def get_bot_config(channel: str) -> dict:
    if channel in bot_configs:
        return bot_configs[channel]
    return {"channel": channel, "prefix": "!", "enabled": False, "welcome_message": None, "auto_mod_enabled": False}


@router.post("/config")
async def set_bot_config(config: BotConfig) -> dict:
    bot_configs[config.channel] = config.model_dump()
    return bot_configs[config.channel]


@router.get("/commands/{channel}")
async def get_commands(channel: str) -> list[dict]:
    return bot_commands.get(channel, [])


@router.post("/commands/{channel}")
async def add_command(channel: str, command: BotCommand) -> dict:
    if channel not in bot_commands:
        bot_commands[channel] = []
    cmd = command.model_dump()
    bot_commands[channel].append(cmd)
    return cmd


@router.delete("/commands/{channel}/{command_name}")
async def delete_command(channel: str, command_name: str) -> dict:
    if channel in bot_commands:
        bot_commands[channel] = [c for c in bot_commands[channel] if c["name"] != command_name]
    return {"status": "deleted"}


@router.put("/commands/{channel}/{command_name}")
async def update_command(channel: str, command_name: str, command: BotCommand) -> dict:
    if channel in bot_commands:
        for i, c in enumerate(bot_commands[channel]):
            if c["name"] == command_name:
                bot_commands[channel][i] = command.model_dump()
                return bot_commands[channel][i]
    return {"error": "Command not found"}


# ========== Moderation ==========
mod_router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@mod_router.get("/rules/{channel}")
async def get_moderation_rules(channel: str) -> list[dict]:
    return moderation_rules.get(channel, [])


@mod_router.post("/rules/{channel}")
async def add_moderation_rule(channel: str, rule: ModerationRule) -> dict:
    if channel not in moderation_rules:
        moderation_rules[channel] = []
    rule_data = rule.model_dump()
    rule_data["id"] = generate_id()
    moderation_rules[channel].append(rule_data)
    return rule_data


@mod_router.put("/rules/{channel}/{rule_id}")
async def update_moderation_rule(channel: str, rule_id: str, rule: ModerationRule) -> dict:
    if channel in moderation_rules:
        for i, r in enumerate(moderation_rules[channel]):
            if r["id"] == rule_id:
                rule_data = rule.model_dump()
                rule_data["id"] = rule_id
                moderation_rules[channel][i] = rule_data
                return rule_data
    return {"error": "Rule not found"}


@mod_router.delete("/rules/{channel}/{rule_id}")
async def delete_moderation_rule(channel: str, rule_id: str) -> dict:
    if channel in moderation_rules:
        moderation_rules[channel] = [r for r in moderation_rules[channel] if r["id"] != rule_id]
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
    
    # Check toxicity
    toxic_count = sum(1 for p in toxic_patterns if p in text)
    if toxic_count > 0:
        confidence = min(0.5 + toxic_count * 0.15, 0.98)
        if confidence > 0.6:
            flagged = True
            reason = f"AI: Toxicity detected ({confidence:.2f})"
            action = "delete"

    # Check spam
    spam_count = sum(1 for p in spam_patterns if p in text)
    if spam_count > 0:
        confidence = min(0.7 + spam_count * 0.1, 0.99)
        flagged = True
        reason = "Link spam detected"
        action = "delete"

    # Check caps
    if len(msg.message) > 10:
        caps_ratio = sum(1 for c in msg.message if c.isupper()) / len(msg.message)
        if caps_ratio > 0.7:
            flagged = True
            confidence = caps_ratio
            reason = f"Excessive caps ({int(caps_ratio * 100)}%)"
            action = "warn"

    # Check repeated chars
    if any(c * 8 in text for c in "abcdefghijklmnopqrstuvwxyz!?"):
        flagged = True
        confidence = 0.85
        reason = "Spam: Repeated characters"
        action = "delete"

    return ModerationResult(flagged=flagged, reason=reason, action=action, confidence=confidence)
