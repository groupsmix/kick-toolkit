"""Chat logs router."""

import logging

from fastapi import APIRouter, Query, Depends
from typing import Optional

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import ChatLogEntry
from app.repositories import chatlogs as chatlogs_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatlogs", tags=["chatlogs"])


@router.get("")
async def get_chat_logs(
    channel: Optional[str] = None,
    username: Optional[str] = None,
    flagged_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    session: dict = Depends(require_auth),
) -> dict:
    if channel:
        require_channel_owner(session, channel)
    logs, total = await chatlogs_repo.query_logs(
        channel=channel, username=username, flagged_only=flagged_only,
        search=search, limit=limit, offset=offset,
    )
    return {"logs": logs, "total": total, "limit": limit, "offset": offset}


@router.get("/user/{username}")
async def get_user_logs(username: str, session: dict = Depends(require_auth)) -> dict:
    return await chatlogs_repo.get_user_logs(username)


@router.post("")
async def add_chat_log(entry: ChatLogEntry, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, entry.channel)
    result = await chatlogs_repo.insert_log(
        channel=entry.channel, username=entry.username,
        message=entry.message, timestamp=entry.timestamp,
        flagged=entry.flagged, flag_reason=entry.flag_reason,
    )
    logger.info("Chat log added: user=%s channel=%s", entry.username, entry.channel)
    return result


@router.get("/stats/{channel}")
async def get_chat_stats(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    return await chatlogs_repo.get_stats(channel)
