"""Discord Bot Integration router."""

import logging

from fastapi import APIRouter, Depends

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import DiscordBotConfigUpdate
from app.repositories import discord_bot as discord_bot_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discord", tags=["discord-bot"])


@router.get("/config/{channel}")
async def get_config(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    config = await discord_bot_repo.get_config(channel)
    if not config:
        return {"channel": channel, "configured": False}
    return config


@router.put("/config/{channel}")
async def update_config(
    channel: str,
    body: DiscordBotConfigUpdate,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    result = await discord_bot_repo.upsert_config(
        channel, **body.model_dump(exclude_none=True),
    )
    logger.info("Discord config updated for channel=%s", channel)
    return result


@router.get("/status/{channel}")
async def get_status(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    return await discord_bot_repo.get_status(channel)
