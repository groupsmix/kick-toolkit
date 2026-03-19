"""Viewer Count Tracker router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth
from app.repositories import viewer_count as vc_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/viewer-count", tags=["viewer-count"])


@router.get("/{channel}/history")
async def get_history(
    channel: str,
    limit: int = Query(default=100, le=500),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await vc_repo.get_history(channel, limit)


@router.get("/{channel}/stats")
async def get_stats(channel: str, _session: dict = Depends(require_auth)) -> dict:
    return await vc_repo.get_stats(channel)


@router.post("/{channel}/snapshot")
async def record_snapshot(
    channel: str, viewer_count: int = Query(...),
    _session: dict = Depends(require_auth),
) -> dict:
    result = await vc_repo.record_snapshot(channel, viewer_count)
    return result
