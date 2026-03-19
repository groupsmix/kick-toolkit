"""Game Challenge System router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import GameChallengeCreate
from app.repositories import game_challenges as gc_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game-challenges", tags=["game-challenges"])


@router.get("/{channel}")
async def list_challenges(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await gc_repo.list_challenges(channel, status)


@router.post("/{channel}")
async def create_challenge(
    channel: str, body: GameChallengeCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await gc_repo.create_challenge(
        channel=channel, title=body.title, description=body.description,
        reward_points=body.reward_points, creator_username=body.creator_username,
    )
    logger.info("Game challenge '%s' created for channel=%s", body.title, channel)
    return result


@router.post("/{channel}/{challenge_id}/accept")
async def accept_challenge(
    channel: str, challenge_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gc_repo.update_status(channel, challenge_id, "accepted")
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return result


@router.post("/{channel}/{challenge_id}/complete")
async def complete_challenge(
    channel: str, challenge_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gc_repo.update_status(channel, challenge_id, "completed")
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return result


@router.post("/{channel}/{challenge_id}/fail")
async def fail_challenge(
    channel: str, challenge_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gc_repo.update_status(channel, challenge_id, "failed")
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return result


@router.post("/{channel}/{challenge_id}/reject")
async def reject_challenge(
    channel: str, challenge_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await gc_repo.update_status(channel, challenge_id, "rejected")
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return result


@router.delete("/{channel}/{challenge_id}")
async def delete_challenge(
    channel: str, challenge_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await gc_repo.delete_challenge(channel, challenge_id)
    return {"status": "deleted"}
