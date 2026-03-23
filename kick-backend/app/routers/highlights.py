"""Auto-Highlight Detection router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth, require_channel_owner
from app.repositories import highlights as highlights_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/highlights", tags=["highlights"])


@router.get("/summary/{channel}")
async def get_summary(
    channel: str,
    session_id: str | None = Query(default=None),
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    return await highlights_repo.get_summary(channel, session_id=session_id)


@router.get("/list/{channel}")
async def get_highlights(
    channel: str,
    session_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await highlights_repo.get_highlights(channel, session_id=session_id, limit=limit)


@router.delete("/{highlight_id}")
async def delete_highlight(
    highlight_id: str, _session: dict = Depends(require_auth)
) -> dict:
    deleted = await highlights_repo.delete_highlight(highlight_id)
    if not deleted:
        return {"error": "Highlight not found"}
    return {"deleted": True}
