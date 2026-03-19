"""Bot configuration and commands router."""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import BotConfig, BotCommand, ModerationRule, ChatMessage, ModerationResult
from app.repositories import bot as bot_repo

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODERATION_URL = "https://api.openai.com/v1/moderations"

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


_CATEGORY_ACTION_MAP: dict[str, str] = {
    "hate": "delete",
    "hate/threatening": "ban",
    "harassment": "delete",
    "harassment/threatening": "ban",
    "self-harm": "delete",
    "self-harm/intent": "delete",
    "self-harm/instructions": "delete",
    "sexual": "delete",
    "sexual/minors": "ban",
    "violence": "delete",
    "violence/graphic": "delete",
}


@mod_router.post("/analyze")
async def analyze_message(msg: ChatMessage) -> ModerationResult:
    """Analyze a chat message using the OpenAI Moderation API."""
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            OPENAI_MODERATION_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"input": msg.message},
        )

    if response.status_code != 200:
        logger.error("OpenAI Moderation API error: %s %s", response.status_code, response.text)
        raise HTTPException(status_code=502, detail="Moderation API request failed")

    data = response.json()
    result = data["results"][0]
    flagged: bool = result["flagged"]
    categories: dict[str, bool] = result["categories"]
    category_scores: dict[str, float] = result["category_scores"]

    reason = None
    action = None
    confidence = 0.0

    if flagged:
        flagged_cats = [cat for cat, val in categories.items() if val]
        top_cat = max(flagged_cats, key=lambda c: category_scores.get(c, 0.0))
        confidence = category_scores.get(top_cat, 0.0)
        reason = f"AI: {', '.join(flagged_cats)} (confidence {confidence:.2f})"
        action = _CATEGORY_ACTION_MAP.get(top_cat, "delete")

    return ModerationResult(
        flagged=flagged,
        reason=reason,
        action=action,
        confidence=confidence,
        categories=categories,
        category_scores=category_scores,
    )
