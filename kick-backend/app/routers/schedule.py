"""Stream Schedule router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import ScheduleEntryCreate, ScheduleEntryUpdate
from app.repositories import schedule as schedule_repo

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
