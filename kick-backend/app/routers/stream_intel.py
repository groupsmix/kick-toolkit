"""Stream Intelligence Dashboard router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth
from app.models.schemas import StreamIntelSessionCreate
from app.repositories import stream_intel as stream_intel_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stream-intel", tags=["stream-intelligence"])


@router.get("/overview/{channel}")
async def get_overview(channel: str, _session: dict = Depends(require_auth)) -> dict:
    return await stream_intel_repo.get_overview(channel)


@router.get("/sessions/{channel}")
async def get_sessions(
    channel: str,
    limit: int = Query(default=20, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await stream_intel_repo.get_sessions(channel, limit)


@router.post("/sessions")
async def create_session(
    body: StreamIntelSessionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await stream_intel_repo.create_session(
        channel=body.channel,
        duration_minutes=body.duration_minutes,
        peak_viewers=body.peak_viewers,
        avg_viewers=body.avg_viewers,
        chat_messages=body.chat_messages,
        new_followers=body.new_followers,
        new_subscribers=body.new_subscribers,
        game=body.game,
        title=body.title,
    )
    logger.info("Stream session recorded for channel=%s score=%.1f",
                body.channel, result["stream_score"])
    return result


@router.get("/score/{channel}")
async def get_score(channel: str, _session: dict = Depends(require_auth)) -> dict:
    score = await stream_intel_repo.get_stream_score(channel)
    if not score:
        return {
            "channel": channel, "overall_score": 0, "viewer_score": 0,
            "chat_score": 0, "growth_score": 0, "consistency_score": 0, "trend": "stable",
        }
    return score


@router.get("/best-times/{channel}")
async def get_best_times(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await stream_intel_repo.get_best_times(channel)
