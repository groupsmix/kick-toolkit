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


# ---------------------------------------------------------------------------
# Viewer Count Tracker (Historical Graphs)
# ---------------------------------------------------------------------------

@router.get("/viewercount/{channel}")
async def get_viewer_count_history(
    channel: str,
    period: str = Query(default="week", regex="^(day|week|month)$"),
    _session: dict = Depends(require_auth),
) -> dict:
    """Return time-series viewer data for historical graphs."""
    from app.services.db import get_conn

    async with get_conn() as conn:
        # Get data from heatmap_snapshots (per-minute granularity)
        cur = await conn.execute(
            """SELECT timestamp, viewer_count, chatter_count
               FROM heatmap_snapshots
               WHERE channel = %s
               ORDER BY timestamp DESC LIMIT %s""",
            (channel, {"day": 1440, "week": 10080, "month": 43200}[period]),
        )
        snapshots = [dict(r) for r in await cur.fetchall()]

        # Get session data for peak/avg context
        cur = await conn.execute(
            """SELECT started_at, ended_at, peak_viewers, avg_viewers, duration_minutes, title, game
               FROM stream_intel_sessions
               WHERE channel = %s
               ORDER BY started_at DESC LIMIT 20""",
            (channel,),
        )
        sessions = [dict(r) for r in await cur.fetchall()]

        # Get overall stats from snapshots
        cur = await conn.execute(
            """SELECT
                 MAX(peak_viewers) AS all_time_peak,
                 AVG(avg_viewers) AS avg_viewers,
                 SUM(hours_streamed) AS total_hours
               FROM streamer_snapshots WHERE channel = %s""",
            (channel,),
        )
        stats_row = await cur.fetchone()

    stats = dict(stats_row) if stats_row else {}
    snapshots.reverse()  # chronological order

    return {
        "channel": channel,
        "period": period,
        "viewer_timeline": snapshots,
        "sessions": sessions,
        "stats": {
            "all_time_peak": stats.get("all_time_peak") or 0,
            "avg_viewers": round(float(stats.get("avg_viewers") or 0), 1),
            "total_hours_streamed": round(float(stats.get("total_hours") or 0), 1),
        },
    }
