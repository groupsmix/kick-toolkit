"""Kill/Death Counter router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import KDCounterUpdate
from app.repositories import kd_counter as kd_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kd-counter", tags=["kd-counter"])


@router.get("/{channel}")
async def get_counter(channel: str, _session: dict = Depends(require_auth)) -> dict:
    counter = await kd_repo.get_counter(channel)
    if not counter:
        return {"channel": channel, "kills": 0, "deaths": 0, "assists": 0, "game": ""}
    return counter


@router.post("/{channel}")
async def create_counter(
    channel: str, game: str = Query(default=""),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await kd_repo.create_counter(channel, game)
    logger.info("K/D counter created for channel=%s", channel)
    return result


@router.put("/{channel}/{counter_id}")
async def update_counter(
    channel: str, counter_id: str, body: KDCounterUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await kd_repo.update_counter(channel, counter_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Counter not found")
    return result


@router.post("/{channel}/{counter_id}/increment")
async def increment_counter(
    channel: str, counter_id: str,
    field: str = Query(..., pattern="^(kills|deaths|assists)$"),
    amount: int = Query(default=1),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await kd_repo.increment(channel, counter_id, field, amount)
    if not result:
        raise HTTPException(status_code=404, detail="Counter not found")
    return result


@router.post("/{channel}/{counter_id}/reset")
async def reset_counter(
    channel: str, counter_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await kd_repo.reset_counter(channel, counter_id)
    if not result:
        raise HTTPException(status_code=404, detail="Counter not found")
    return result
