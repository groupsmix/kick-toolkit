"""Bot configuration, commands, timed messages, welcome messages, and shoutout router."""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import (
    BotConfig,
    BotCommand,
    ModerationRule,
    ChatMessage,
    ModerationResult,
    CommandExecuteRequest,
    CommandExecuteResult,
    TimedMessageCreate,
    TimedMessageUpdate,
    WelcomeCheckRequest,
    WelcomeCheckResult,
    ShoutoutRequest,
    ShoutoutResult,
)
from app.repositories import bot as bot_repo
from app.services.kick_api import (
    COMMAND_VARIABLES,
    resolve_variables,
    get_user_profile,
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODERATION_URL = "https://api.openai.com/v1/moderations"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bot", tags=["bot"])


@router.get("/config/{channel}")
async def get_bot_config(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    config = await bot_repo.get_config(channel)
    if config:
        return dict(config)
    return {
        "channel": channel,
        "prefix": "!",
        "enabled": False,
        "welcome_message": None,
        "auto_mod_enabled": False,
        "welcome_enabled": False,
        "welcome_new_message": None,
        "welcome_returning_message": None,
        "welcome_subscriber_message": None,
        "shoutout_template": "Check out {target} at kick.com/{target}! They were last playing {game}.",
        "auto_shoutout_raiders": False,
    }


@router.put("/config")
async def set_bot_config(config: BotConfig, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, config.channel)
    await bot_repo.upsert_config(
        config.channel, config.prefix, config.enabled,
        config.welcome_message, config.auto_mod_enabled,
        config.welcome_enabled, config.welcome_new_message,
        config.welcome_returning_message, config.welcome_subscriber_message,
    )
    logger.info("Bot config updated for channel=%s", config.channel)
    return config.model_dump()


@router.get("/commands/{channel}")
async def get_commands(channel: str, session: dict = Depends(require_auth)) -> list[dict]:
    require_channel_owner(session, channel)
    return await bot_repo.list_commands(channel)


@router.post("/commands/{channel}")
async def add_command(channel: str, command: BotCommand, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await bot_repo.create_command(
        channel, command.name, command.response,
        command.cooldown, command.enabled, command.mod_only,
    )
    logger.info("Command !%s added for channel=%s", command.name, channel)
    return command.model_dump()


@router.delete("/commands/{channel}/{command_name}")
async def delete_command(channel: str, command_name: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await bot_repo.delete_command(channel, command_name)
    logger.info("Command !%s deleted from channel=%s", command_name, channel)
    return {"status": "deleted"}


@router.put("/commands/{channel}/{command_name}")
async def update_command(channel: str, command_name: str, command: BotCommand, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    updated = await bot_repo.update_command(
        channel, command_name, command.name, command.response,
        command.cooldown, command.enabled, command.mod_only,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Command not found")
    logger.info("Command !%s updated in channel=%s", command_name, channel)
    return updated


# ========== Command Variables ==========

@router.get("/commands/variables/list")
async def list_command_variables(session: dict = Depends(require_auth)) -> list[dict]:
    """Return the list of supported command variables."""
    return COMMAND_VARIABLES


@router.post("/commands/{channel}/execute")
async def execute_command(channel: str, req: CommandExecuteRequest, session: dict = Depends(require_auth)) -> CommandExecuteResult:
    """Execute a command and resolve variables in its response."""
    require_channel_owner(session, channel)
    commands = await bot_repo.list_commands(channel)
    cmd = next((c for c in commands if c["name"] == req.command_name), None)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Command !{req.command_name} not found")

    resolved = await resolve_variables(cmd["response"], channel, req.username)
    return CommandExecuteResult(
        command_name=req.command_name,
        original_response=cmd["response"],
        resolved_response=resolved,
    )


# ========== Timed Messages ==========

@router.get("/timed/{channel}")
async def get_timed_messages(channel: str, session: dict = Depends(require_auth)) -> list[dict]:
    require_channel_owner(session, channel)
    return await bot_repo.list_timed_messages(channel)


@router.post("/timed/{channel}")
async def create_timed_message(channel: str, msg: TimedMessageCreate, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    msg_id = await bot_repo.create_timed_message(
        channel, msg.message, msg.interval_minutes, msg.enabled,
    )
    logger.info("Timed message %s created for channel=%s", msg_id, channel)
    return {"id": msg_id, "channel": channel, **msg.model_dump()}


@router.put("/timed/{channel}/{msg_id}")
async def update_timed_message(channel: str, msg_id: str, msg: TimedMessageUpdate, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    updated = await bot_repo.update_timed_message(
        channel, msg_id, msg.message, msg.interval_minutes, msg.enabled,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Timed message not found")
    logger.info("Timed message %s updated in channel=%s", msg_id, channel)
    return updated


@router.delete("/timed/{channel}/{msg_id}")
async def delete_timed_message(channel: str, msg_id: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await bot_repo.delete_timed_message(channel, msg_id)
    logger.info("Timed message %s deleted from channel=%s", msg_id, channel)
    return {"status": "deleted"}


# ========== Welcome Messages ==========

@router.post("/welcome/check")
async def check_welcome(req: WelcomeCheckRequest, _session: dict = Depends(require_auth)) -> WelcomeCheckResult:
    """Determine which welcome message to send for a given user."""
    user_data = _session.get("user_data", {})
    channel = user_data.get("streamer_channel") or user_data.get("name", "")

    if not channel:
        raise HTTPException(status_code=400, detail="Channel not found in session")

    config = await bot_repo.get_config(channel)
    if not config or not config.get("welcome_enabled"):
        return WelcomeCheckResult(username=req.username, welcome_type="none", message=None)

    welcome_type = await bot_repo.check_welcome_type(channel, req.username)

    message = None
    if welcome_type == "new":
        message = config.get("welcome_new_message")
    elif welcome_type == "subscriber":
        message = config.get("welcome_subscriber_message")
    elif welcome_type == "returning":
        message = config.get("welcome_returning_message")

    if message:
        message = message.replace("{username}", req.username)

    return WelcomeCheckResult(
        username=req.username,
        welcome_type=welcome_type,
        message=message,
    )


# ========== Shoutout ==========

@router.post("/shoutout/{channel}")
async def shoutout(channel: str, req: ShoutoutRequest, session: dict = Depends(require_auth)) -> ShoutoutResult:
    """Generate a shoutout message for a target user by fetching their Kick profile."""
    require_channel_owner(session, channel)
    profile = await get_user_profile(req.target_username)

    config = await bot_repo.get_config(channel)
    template = "Check out {target} at kick.com/{target}! They were last playing {game}."
    if config and config.get("shoutout_template"):
        template = config["shoutout_template"]

    game = profile.get("game", "Unknown") if profile else "Unknown"
    title = profile.get("title", "") if profile else ""
    follower_count = profile.get("follower_count", 0) if profile else 0
    avatar_url = profile.get("avatar_url") if profile else None
    is_live = profile.get("is_live", False) if profile else False

    message = (
        template
        .replace("{target}", req.target_username)
        .replace("{game}", game or "Unknown")
        .replace("{title}", title or "")
        .replace("{followers}", str(follower_count))
    )

    return ShoutoutResult(
        target_username=req.target_username,
        message=message,
        avatar_url=avatar_url,
        is_live=is_live,
        game=game,
        title=title,
        follower_count=follower_count,
    )


# ========== Moderation ==========
mod_router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@mod_router.get("/rules/{channel}")
async def get_moderation_rules(channel: str, session: dict = Depends(require_auth)) -> list[dict]:
    require_channel_owner(session, channel)
    return await bot_repo.list_moderation_rules(channel)


@mod_router.post("/rules/{channel}")
async def add_moderation_rule(channel: str, rule: ModerationRule, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    rule_id = await bot_repo.create_moderation_rule(
        channel, rule.name, rule.type, rule.enabled,
        rule.action, rule.severity, rule.settings,
    )
    logger.info("Moderation rule '%s' created for channel=%s", rule.name, channel)
    result = rule.model_dump()
    result["id"] = rule_id
    return result


@mod_router.put("/rules/{channel}/{rule_id}")
async def update_moderation_rule(channel: str, rule_id: str, rule: ModerationRule, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    updated = await bot_repo.update_moderation_rule(
        channel, rule_id, rule.name, rule.type, rule.enabled,
        rule.action, rule.severity, rule.settings,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    logger.info("Moderation rule '%s' updated in channel=%s", rule.name, channel)
    return updated


@mod_router.delete("/rules/{channel}/{rule_id}")
async def delete_moderation_rule(channel: str, rule_id: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
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


_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _http_client


async def close_http_client() -> None:
    """Close the module-level HTTP client, releasing TCP connections."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


@mod_router.post("/analyze")
async def analyze_message(
    msg: ChatMessage,
    _session: dict = Depends(require_auth),
) -> ModerationResult:
    """Analyze a chat message using the OpenAI Moderation API."""
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Moderation service unavailable",
        )

    if len(msg.message) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 chars)")

    client = _get_http_client()
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
