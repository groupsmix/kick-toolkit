"""Game Queue System router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import GameQueueCreate, GameQueueEntry
from app.repositories import game_queue as gq_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game-queue", tags=["game-queue"])


@router.get("/{channel}")
async def get_queue(channel: str, _session: dict = Depends(require_auth)) -> dict:
    queue = await gq_repo.get_queue(channel)
    if not queue:
        return {"channel": channel, "status": "none", "entries": []}
    return queue


@router.post("/{channel}")
async def create_queue(
    channel: str, body: GameQueueCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gq_repo.create_queue(channel, body.game, body.max_size)
    logger.info("Game queue created for channel=%s game=%s", channel, body.game)
    return result


@router.post("/{channel}/{queue_id}/join")
async def join_queue(
    channel: str, queue_id: str, body: GameQueueEntry,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gq_repo.join_queue(channel, queue_id, body.username, body.note)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot join queue. It may be full or closed.")
    return result


@router.post("/{channel}/{queue_id}/leave")
async def leave_queue(
    channel: str, queue_id: str, username: str = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gq_repo.leave_queue(channel, queue_id, username)
    if not result:
        raise HTTPException(status_code=404, detail="Queue not found")
    return result


@router.post("/{channel}/{queue_id}/close")
async def close_queue(
    channel: str, queue_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gq_repo.close_queue(channel, queue_id)
    if not result:
        raise HTTPException(status_code=404, detail="Queue not found")
    return result


@router.post("/{channel}/{queue_id}/pick-teams")
async def pick_teams(
    channel: str, queue_id: str,
    team_count: int = Query(default=2, ge=2, le=10),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await gq_repo.pick_teams(channel, queue_id, team_count)
    return result
