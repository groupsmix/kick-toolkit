"""Song Request System router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import SongQueueSettingsUpdate, SongRequestCreate
from app.repositories import songs as songs_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/songs", tags=["songs"])


@router.get("/settings/{channel}")
async def get_settings(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    settings = await songs_repo.get_settings(channel)
    if settings:
        return settings
    return {
        "channel": channel, "enabled": True, "max_queue_size": 50,
        "max_duration_seconds": 600, "allow_duplicates": False,
        "subscriber_only": False, "cost_per_request": 0,
    }


@router.post("/settings/{channel}")
async def update_settings(
    channel: str, body: SongQueueSettingsUpdate, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await songs_repo.upsert_settings(
        channel=channel,
        enabled=body.enabled,
        max_queue_size=body.max_queue_size,
        max_duration_seconds=body.max_duration_seconds,
        allow_duplicates=body.allow_duplicates,
        subscriber_only=body.subscriber_only,
        cost_per_request=body.cost_per_request,
    )
    logger.info("Song queue settings updated for channel=%s", channel)
    return result


@router.get("/queue/{channel}")
async def get_queue(channel: str, session: dict = Depends(require_auth)) -> list[dict]:
    require_channel_owner(session, channel)
    return await songs_repo.get_queue(channel)


@router.post("/queue/{channel}")
async def add_request(
    channel: str, body: SongRequestCreate, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await songs_repo.add_request(
        channel=channel, username=body.username, title=body.title,
        artist=body.artist, url=body.url, platform=body.platform,
        duration_seconds=body.duration_seconds,
    )
    logger.info("Song '%s' requested by %s in channel=%s", body.title, body.username, channel)
    return result


@router.post("/queue/{channel}/{song_id}/skip")
async def skip_song(
    channel: str, song_id: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await songs_repo.skip_song(channel, song_id)
    if not result:
        raise HTTPException(status_code=404, detail="Song not found")
    return result


@router.post("/queue/{channel}/{song_id}/play")
async def play_song(
    channel: str, song_id: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await songs_repo.play_song(channel, song_id)
    if not result:
        raise HTTPException(status_code=404, detail="Song not found")
    return result


@router.delete("/queue/{channel}/{song_id}")
async def remove_request(
    channel: str, song_id: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    await songs_repo.remove_request(channel, song_id)
    return {"status": "removed"}


@router.delete("/queue/{channel}")
async def clear_queue(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    count = await songs_repo.clear_queue(channel)
    logger.info("Queue cleared for channel=%s (%d songs)", channel, count)
    return {"status": "cleared", "removed": count}


@router.get("/history/{channel}")
async def get_history(
    channel: str,
    limit: int = Query(default=50, le=200),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await songs_repo.get_history(channel, limit)
