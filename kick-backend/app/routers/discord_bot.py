"""Discord Bot Integration router — settings, webhook events, test notifications."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import DiscordSettingsUpdate, DiscordWebhookTest
from app.repositories import discord_bot as discord_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discord", tags=["discord-bot"])


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@router.get("/settings/{channel}")
async def get_settings(channel: str, _session: dict = Depends(require_auth)) -> dict:
    result = await discord_repo.get_settings(channel)
    if not result:
        return {
            "channel": channel, "enabled": False,
            "guild_id": "", "webhook_url": "",
            "go_live_notifications": True, "go_live_channel_id": "",
            "go_live_message": "",
            "chat_bridge_enabled": False, "chat_bridge_channel_id": "",
            "sub_sync_enabled": False, "sub_sync_role_id": "",
            "stats_command_enabled": True, "schedule_command_enabled": True,
        }
    return result


@router.put("/settings/{channel}")
async def update_settings(
    channel: str, body: DiscordSettingsUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await discord_repo.upsert_settings(channel, **updates)
    logger.info("Discord settings updated for channel=%s", channel)
    return result


# ---------------------------------------------------------------------------
# Webhook Events
# ---------------------------------------------------------------------------

@router.get("/events/{channel}")
async def list_events(
    channel: str,
    limit: int = Query(default=50, le=200),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await discord_repo.list_events(channel, limit)


@router.get("/event/{event_id}")
async def get_event(event_id: str, _session: dict = Depends(require_auth)) -> dict:
    result = await discord_repo.get_event(event_id)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


# ---------------------------------------------------------------------------
# Test Notification
# ---------------------------------------------------------------------------

@router.post("/test")
async def test_webhook(
    body: DiscordWebhookTest, _session: dict = Depends(require_auth)
) -> dict:
    settings = await discord_repo.get_settings(body.channel)
    if not settings or not settings.get("webhook_url"):
        raise HTTPException(status_code=400, detail="Discord webhook URL not configured")

    event = await discord_repo.create_event(
        channel=body.channel,
        event_type=body.event_type,
        payload={"test": True, "message": f"Test {body.event_type} notification from KickTools"},
    )
    logger.info("Test webhook event created for channel=%s type=%s", body.channel, body.event_type)
    return event
