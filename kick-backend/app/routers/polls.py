"""Chat Polls & Voting router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import PollCreate, PollVote
from app.repositories import polls as polls_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/polls", tags=["polls"])


@router.post("/{channel}")
async def create_poll(
    channel: str, body: PollCreate, _session: dict = Depends(require_auth)
) -> dict:
    if len(body.options) < 2:
        raise HTTPException(status_code=400, detail="Poll must have at least 2 options")
    if len(body.options) > 10:
        raise HTTPException(status_code=400, detail="Poll can have at most 10 options")
    result = await polls_repo.create_poll(
        channel, body.title, body.options, body.duration_seconds,
        body.allow_multiple_votes,
    )
    logger.info("Poll '%s' created for channel=%s", body.title, channel)
    return result


@router.get("/{channel}")
async def list_polls(
    channel: str,
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await polls_repo.list_polls(channel, limit)


@router.get("/{channel}/{poll_id}")
async def get_poll(
    channel: str, poll_id: str, _session: dict = Depends(require_auth)
) -> dict:
    poll = await polls_repo.get_poll(channel, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll


@router.post("/{channel}/{poll_id}/vote")
async def cast_vote(
    channel: str, poll_id: str, body: PollVote,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await polls_repo.cast_vote(channel, poll_id, body.username, body.option_index)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot vote. Poll may be closed, option invalid, or already voted.",
        )
    logger.info("Vote cast by %s on poll %s in channel=%s", body.username, poll_id, channel)
    return result


@router.post("/{channel}/{poll_id}/close")
async def close_poll(
    channel: str, poll_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await polls_repo.close_poll(channel, poll_id)
    if not result:
        raise HTTPException(status_code=404, detail="Poll not found")
    logger.info("Poll %s closed in channel=%s", poll_id, channel)
    return result


@router.get("/{channel}/{poll_id}/results")
async def get_results(
    channel: str, poll_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await polls_repo.get_results(channel, poll_id)
    if not result:
        raise HTTPException(status_code=404, detail="Poll not found")
    return result
