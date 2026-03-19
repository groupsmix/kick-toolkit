"""Viewer CRM router — profiles, segments, churn detection, shoutout suggestions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import ViewerProfileUpdate
from app.repositories import viewer_crm as crm_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["viewer-crm"])


# ---------------------------------------------------------------------------
# Viewer Profiles
# ---------------------------------------------------------------------------

@router.get("/viewers/{channel}")
async def list_viewers(
    channel: str,
    segment: str = Query(default=None),
    sort_by: str = Query(default="last_seen"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    _session: dict = Depends(require_auth),
) -> dict:
    viewers = await crm_repo.list_profiles(channel, segment, sort_by, limit, offset)
    total = await crm_repo.get_viewer_count(channel)
    return {"viewers": viewers, "total": total}


@router.get("/viewer/{channel}/{username}")
async def get_viewer(
    channel: str, username: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await crm_repo.get_profile(channel, username)
    if not result:
        raise HTTPException(status_code=404, detail="Viewer not found")
    return result


@router.put("/viewer/{channel}/{username}")
async def update_viewer(
    channel: str, username: str, body: ViewerProfileUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await crm_repo.update_profile(channel, username, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Viewer not found")
    return result


# ---------------------------------------------------------------------------
# Segments & Analytics
# ---------------------------------------------------------------------------

@router.get("/segments/{channel}")
async def get_segments(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await crm_repo.get_segment_summary(channel)


@router.get("/churn-risks/{channel}")
async def get_churn_risks(
    channel: str,
    days: int = Query(default=7, le=90),
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await crm_repo.get_churn_risks(channel, days, limit)


@router.get("/shoutouts/{channel}")
async def get_shoutout_suggestions(
    channel: str,
    limit: int = Query(default=10, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await crm_repo.get_shoutout_suggestions(channel, limit)
