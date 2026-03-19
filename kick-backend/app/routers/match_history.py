"""Match History Tracker router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth
from app.models.schemas import MatchRecordCreate
from app.repositories import match_history as mh_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/match-history", tags=["match-history"])


@router.get("/{channel}")
async def list_matches(
    channel: str,
    game: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await mh_repo.list_matches(channel, game, limit)


@router.post("/{channel}")
async def create_match(
    channel: str, body: MatchRecordCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await mh_repo.create_match(
        channel=channel, game=body.game, opponent=body.opponent,
        result=body.result, score=body.score, notes=body.notes,
    )
    logger.info("Match recorded for channel=%s: %s vs %s = %s", channel, body.game, body.opponent, body.result)
    return result


@router.get("/{channel}/stats")
async def get_stats(
    channel: str,
    game: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> dict:
    return await mh_repo.get_stats(channel, game)


@router.delete("/{channel}/{match_id}")
async def delete_match(
    channel: str, match_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await mh_repo.delete_match(channel, match_id)
    return {"status": "deleted"}
