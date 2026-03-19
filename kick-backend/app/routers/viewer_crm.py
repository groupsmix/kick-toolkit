"""Viewer CRM router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth
from app.models.schemas import ViewerProfileUpdate
from app.repositories import viewer_crm as viewer_crm_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/viewer-crm", tags=["viewer-crm"])


@router.get("/overview/{channel}")
async def get_overview(channel: str, _session: dict = Depends(require_auth)) -> dict:
    return await viewer_crm_repo.get_overview(channel)


@router.get("/viewers/{channel}")
async def get_viewers(
    channel: str,
    segment: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await viewer_crm_repo.get_viewers(channel, segment=segment, limit=limit)


@router.get("/viewer/{channel}/{username}")
async def get_viewer(
    channel: str, username: str, _session: dict = Depends(require_auth)
) -> dict:
    viewer = await viewer_crm_repo.get_viewer(channel, username)
    if not viewer:
        return {"error": "Viewer not found"}
    return viewer


@router.put("/viewer/{channel}/{username}")
async def update_viewer(
    channel: str, username: str,
    body: ViewerProfileUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    result = await viewer_crm_repo.update_viewer(
        channel, username, notes=body.notes, segment=body.segment,
    )
    if not result:
        return {"error": "Viewer not found"}
    logger.info("Updated viewer %s for channel %s", username, channel)
    return result


@router.get("/segments/{channel}")
async def get_segments(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await viewer_crm_repo.get_segment_summary(channel)
