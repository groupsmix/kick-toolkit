"""Predictive Analytics router — growth predictions, comparisons, and stock market."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import SnapshotCreate
from app.repositories import analytics as analytics_repo
from app.services import analytics as analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

@router.get("/overview/{channel}")
async def get_overview(channel: str, _session: dict = Depends(require_auth)) -> dict:
    return await analytics_service.compute_overview(channel)


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

@router.post("/snapshots")
async def create_snapshot(
    body: SnapshotCreate, _session: dict = Depends(require_auth)
) -> dict:
    snap = await analytics_repo.create_snapshot(
        channel=body.channel,
        avg_viewers=body.avg_viewers,
        peak_viewers=body.peak_viewers,
        follower_count=body.follower_count,
        subscriber_count=body.subscriber_count,
        hours_streamed=body.hours_streamed,
        chat_messages=body.chat_messages,
        categories=body.categories,
    )
    logger.info("Snapshot recorded for channel=%s", body.channel)
    return snap


@router.get("/snapshots/{channel}")
async def get_snapshots(
    channel: str,
    limit: int = Query(default=30, le=90),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await analytics_repo.get_snapshots(channel, limit)


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------

@router.post("/predictions/{channel}")
async def generate_predictions(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    predictions = await analytics_service.generate_predictions(channel)
    if not predictions:
        raise HTTPException(
            status_code=400,
            detail="Not enough data to generate predictions. Record at least 2 snapshots.",
        )
    return predictions


@router.get("/predictions/{channel}")
async def get_predictions(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await analytics_repo.get_predictions(channel)


# ---------------------------------------------------------------------------
# Growth Comparisons
# ---------------------------------------------------------------------------

@router.post("/comparisons/{channel}")
async def generate_comparisons(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await analytics_service.generate_comparisons(channel)


@router.get("/comparisons/{channel}")
async def get_comparisons(
    channel: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await analytics_repo.get_comparisons(channel)


# ---------------------------------------------------------------------------
# Stock Market
# ---------------------------------------------------------------------------

@router.post("/stock/refresh")
async def refresh_stock_scores(_session: dict = Depends(require_auth)) -> list[dict]:
    return await analytics_service.update_stock_scores()


@router.get("/stock/leaderboard")
async def get_stock_leaderboard(
    limit: int = Query(default=20, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await analytics_repo.get_stock_scores(limit)


@router.get("/stock/{channel}")
async def get_stock_score(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    score = await analytics_repo.get_stock_score(channel)
    if not score:
        return {"channel": channel, "stock_score": 0, "trend": "stable", "change_pct": 0, "rank": 0}
    return score


# ---------------------------------------------------------------------------
# AI Growth Narrative
# ---------------------------------------------------------------------------

@router.get("/narrative/{channel}")
async def get_growth_narrative(
    channel: str, _session: dict = Depends(require_auth)
) -> dict:
    narrative = await analytics_service.get_growth_narrative(channel)
    return {"narrative": narrative}
