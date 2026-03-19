"""Achievement Tracker router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import AchievementCreate
from app.repositories import achievements as ach_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("/{channel}")
async def list_achievements(
    channel: str,
    game: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await ach_repo.list_achievements(channel, game)


@router.post("/{channel}")
async def create_achievement(
    channel: str, body: AchievementCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await ach_repo.create_achievement(
        channel=channel, game=body.game, title=body.title,
        description=body.description, icon=body.icon,
    )
    logger.info("Achievement '%s' created for channel=%s", body.title, channel)
    return result


@router.post("/{channel}/{ach_id}/unlock")
async def unlock_achievement(
    channel: str, ach_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await ach_repo.unlock_achievement(channel, ach_id)
    if not result:
        raise HTTPException(status_code=404, detail="Achievement not found")
    logger.info("Achievement %s unlocked for channel=%s", ach_id, channel)
    return result


@router.delete("/{channel}/{ach_id}")
async def delete_achievement(
    channel: str, ach_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await ach_repo.delete_achievement(channel, ach_id)
    return {"status": "deleted"}
