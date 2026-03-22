"""Viewer Heatmap & Attention Tracking router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import ContentSegmentCreate, HeatmapSnapshot
from app.repositories import heatmap as heatmap_repo
from app.services import heatmap as heatmap_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


# ---------------------------------------------------------------------------
# Overview & Insights
# ---------------------------------------------------------------------------

@router.get("/overview/{channel}")
async def get_overview(
    channel: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    return await heatmap_service.compute_overview(channel)


@router.get("/insights/{channel}")
async def get_insights(
    channel: str, session: dict = Depends(require_auth)
) -> list[dict]:
    require_channel_owner(session, channel)
    overview = await heatmap_service.compute_overview(channel)
    return overview.get("insights", [])


# ---------------------------------------------------------------------------
# Timeline & Session Details
# ---------------------------------------------------------------------------

@router.get("/timeline/{session_id}")
async def get_timeline(
    session_id: str, session: dict = Depends(require_auth)
) -> list[dict]:
    return await heatmap_repo.get_heatmap_timeline(session_id)


@router.get("/session/{session_id}")
async def get_session_insights(
    session_id: str,
    channel: str = Query(...),
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    return await heatmap_service.compute_session_insights(channel, session_id)


# ---------------------------------------------------------------------------
# Content Segments
# ---------------------------------------------------------------------------

@router.post("/segments/{session_id}")
async def add_segment(
    session_id: str,
    body: ContentSegmentCreate,
    channel: str = Query(...),
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    return await heatmap_repo.create_segment(
        channel=channel,
        stream_session_id=session_id,
        label=body.label,
        category=body.category,
        started_at=body.started_at,
        ended_at=body.ended_at,
        viewer_count_start=body.viewer_count_start,
        viewer_count_end=body.viewer_count_end,
    )


@router.get("/segments/{session_id}")
async def get_segments(
    session_id: str, session: dict = Depends(require_auth)
) -> list[dict]:
    return await heatmap_repo.get_segments(session_id)


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

@router.post("/snapshot")
async def record_snapshot(
    body: HeatmapSnapshot, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, body.channel)
    await heatmap_repo.record_heatmap_snapshot(
        channel=body.channel,
        stream_session_id=body.stream_session_id,
        minute_offset=body.minute_offset,
        viewer_count=body.viewer_count,
        message_count=body.message_count,
        unique_chatters=body.unique_chatters,
        category=body.category,
    )
    return {"recorded": True}


# ---------------------------------------------------------------------------
# Viewer Sessions
# ---------------------------------------------------------------------------

@router.get("/viewers/{channel}")
async def get_viewer_sessions(
    channel: str,
    session_id: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await heatmap_repo.get_viewer_sessions(channel, session_id, limit)


@router.get("/viewers/{channel}/stats")
async def get_viewer_stats(
    channel: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    return await heatmap_repo.get_viewer_stats(channel)


@router.get("/categories/{channel}")
async def get_category_stats(
    channel: str, session: dict = Depends(require_auth)
) -> list[dict]:
    require_channel_owner(session, channel)
    return await heatmap_repo.get_category_stats(channel)
