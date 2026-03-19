"""Timed Messages router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import TimedMessageCreate, TimedMessageUpdate
from app.repositories import timed_messages as timed_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/timed-messages", tags=["timed-messages"])


@router.get("/{channel}")
async def list_messages(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await timed_repo.list_messages(channel)


@router.post("/{channel}")
async def create_message(
    channel: str, body: TimedMessageCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await timed_repo.create_message(
        channel=channel, message=body.message,
        interval_minutes=body.interval_minutes, enabled=body.enabled,
    )
    logger.info("Timed message created for channel=%s", channel)
    return result


@router.put("/{channel}/{msg_id}")
async def update_message(
    channel: str, msg_id: str, body: TimedMessageUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await timed_repo.update_message(channel, msg_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Timed message not found")
    return result


@router.delete("/{channel}/{msg_id}")
async def delete_message(
    channel: str, msg_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await timed_repo.delete_message(channel, msg_id)
    return {"status": "deleted"}
