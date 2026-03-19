"""Chat Polls & Voting router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import PollCreate, PollVote
from app.repositories import polls as polls_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/polls", tags=["polls"])


@router.get("/{channel}")
async def list_polls(
    channel: str,
    status: str = Query(default=None),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await polls_repo.list_polls(channel, status)


@router.post("/{channel}")
async def create_poll(
    channel: str, body: PollCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await polls_repo.create_poll(
        channel=channel, title=body.title, options=body.options,
        duration_seconds=body.duration_seconds, poll_type=body.poll_type,
    )
    logger.info("Poll '%s' created for channel=%s", body.title, channel)
    return result


@router.post("/{channel}/{poll_id}/vote")
async def vote_on_poll(
    channel: str, poll_id: str, body: PollVote, _session: dict = Depends(require_auth)
) -> dict:
    result = await polls_repo.vote(channel, poll_id, body.username, body.option_index)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot vote. Poll may be closed or you already voted.")
    return result


@router.post("/{channel}/{poll_id}/close")
async def close_poll(
    channel: str, poll_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await polls_repo.close_poll(channel, poll_id)
    if not result:
        raise HTTPException(status_code=404, detail="Poll not found")
    logger.info("Poll %s closed for channel=%s", poll_id, channel)
    return result


@router.delete("/{channel}/{poll_id}")
async def delete_poll(
    channel: str, poll_id: str, _session: dict = Depends(require_auth)
) -> dict:
    await polls_repo.delete_poll(channel, poll_id)
    return {"status": "deleted"}
