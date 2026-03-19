"""Rank Tracker router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import RankTrackerUpdate
from app.repositories import rank_tracker as rt_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rank-tracker", tags=["rank-tracker"])


@router.get("/{channel}")
async def list_ranks(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await rt_repo.list_ranks(channel)


@router.get("/{channel}/{game}")
async def get_rank(channel: str, game: str, _session: dict = Depends(require_auth)) -> dict:
    rank = await rt_repo.get_rank(channel, game)
    if not rank:
        return {"channel": channel, "game": game, "current_rank": "", "peak_rank": "", "rank_points": 0}
    return rank


@router.post("/{channel}")
async def upsert_rank(
    channel: str, body: RankTrackerUpdate, _session: dict = Depends(require_auth)
) -> dict:
    result = await rt_repo.upsert_rank(
        channel=channel, game=body.game, current_rank=body.current_rank,
        rank_points=body.rank_points, peak_rank=body.peak_rank,
    )
    logger.info("Rank updated for channel=%s game=%s: %s", channel, body.game, body.current_rank)
    return result


@router.delete("/{channel}/{game}")
async def delete_rank(
    channel: str, game: str, _session: dict = Depends(require_auth)
) -> dict:
    await rt_repo.delete_rank(channel, game)
    return {"status": "deleted"}
