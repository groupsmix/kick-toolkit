"""Stream Schedule router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import ScheduleEntryCreate, ScheduleEntryUpdate, NotificationSettingsUpdate
from app.repositories import schedule as schedule_repo
from app.repositories import notifications as notifications_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("/{channel}")
async def list_entries(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await schedule_repo.list_entries(channel)


@router.post("/{channel}")
async def create_entry(
    channel: str, body: ScheduleEntryCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await schedule_repo.create_entry(
        channel=channel, day_of_week=body.day_of_week,
        start_time=body.start_time, end_time=body.end_time,
        title=body.title, game=body.game,
        recurring=body.recurring, enabled=body.enabled,
    )
    logger.info("Schedule entry created for channel=%s (day=%d)", channel, body.day_of_week)
    return result


@router.put("/{channel}/{entry_id}")
async def update_entry(
    channel: str, entry_id: str, body: ScheduleEntryUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await schedule_repo.update_entry(channel, entry_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Schedule entry not found")
    logger.info("Schedule entry %s updated for channel=%s", entry_id, channel)
    return result


@router.delete("/{channel}/{entry_id}")
async def delete_entry(
    channel: str, entry_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await schedule_repo.delete_entry(channel, entry_id)
    return {"status": "deleted"}


# Public endpoint for profile pages
@router.get("/public/{channel}")
async def get_public_schedule(channel: str) -> list[dict]:
    return await schedule_repo.get_public_schedule(channel)


# ---------------------------------------------------------------------------
# Go-Live Notifications
# ---------------------------------------------------------------------------

@router.get("/{channel}/notifications/settings")
async def get_notification_settings(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    settings = await notifications_repo.get_notification_settings(channel)
    if not settings:
        return {
            "channel": channel, "go_live_enabled": False,
            "webhook_urls": [], "discord_webhook_url": "",
            "notification_message": "{channel} is now live! Playing {game} — {title}",
            "notify_on_title_change": False, "notify_on_game_change": False,
        }
    return settings


@router.put("/{channel}/notifications/settings")
async def update_notification_settings(
    channel: str, body: NotificationSettingsUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await notifications_repo.upsert_notification_settings(
        channel=channel,
        go_live_enabled=body.go_live_enabled,
        webhook_urls=body.webhook_urls,
        discord_webhook_url=body.discord_webhook_url,
        notification_message=body.notification_message,
        notify_on_title_change=body.notify_on_title_change,
        notify_on_game_change=body.notify_on_game_change,
    )
    logger.info("Notification settings updated for channel=%s", channel)
    return result


@router.post("/{channel}/notify")
async def send_go_live_notification(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    """Trigger a go-live notification to all configured targets."""
    settings = await notifications_repo.get_notification_settings(channel)
    if not settings or not settings.get("go_live_enabled"):
        raise HTTPException(status_code=400, detail="Go-live notifications are not enabled")

    targets = []
    message = settings.get("notification_message", "{channel} is now live!")
    message = message.replace("{channel}", channel)

    # Collect targets
    if settings.get("discord_webhook_url"):
        targets.append(f"discord:{settings['discord_webhook_url'][:30]}...")
    for url in settings.get("webhook_urls", []):
        if url:
            targets.append(f"webhook:{url[:30]}...")

    if not targets:
        raise HTTPException(status_code=400, detail="No notification targets configured")

    # Log the notification
    log_entry = await notifications_repo.log_notification(
        channel=channel,
        notification_type="go_live",
        message=message,
        targets=targets,
    )

    logger.info("Go-live notification sent for channel=%s to %d targets", channel, len(targets))
    return log_entry


@router.get("/{channel}/notifications/history")
async def get_notification_history(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await notifications_repo.get_notification_history(channel)
