"""Stream Intelligence Dashboard router — stream scores, growth, best times."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import StreamIntelSessionCreate, StreamIntelSessionUpdate
from app.repositories import stream_intel as intel_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["stream-intelligence"])


# ---------------------------------------------------------------------------
# Stream Sessions
# ---------------------------------------------------------------------------

@router.post("/sessions")
async def create_session(
    body: StreamIntelSessionCreate, _session: dict = Depends(require_auth)
) -> dict:
    result = await intel_repo.create_session(body.channel, body.started_at, body.game)
    logger.info("Stream intel session created for channel=%s", body.channel)
    return result


@router.get("/sessions/{channel}")
async def list_sessions(
    channel: str,
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await intel_repo.list_sessions(channel, limit)


@router.get("/session/{session_id}")
async def get_session(session_id: str, _session: dict = Depends(require_auth)) -> dict:
    result = await intel_repo.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.put("/session/{session_id}")
async def update_session(
    session_id: str, body: StreamIntelSessionUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await intel_repo.update_session(session_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, _session: dict = Depends(require_auth)) -> dict:
    await intel_repo.delete_session(session_id)
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Growth & Analytics
# ---------------------------------------------------------------------------

@router.get("/growth/{channel}")
async def get_growth(
    channel: str,
    days: int = Query(default=30, le=365),
    _session: dict = Depends(require_auth),
) -> dict:
    return await intel_repo.get_growth_metrics(channel, days)


@router.get("/best-times/{channel}")
async def get_best_times(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await intel_repo.get_best_time_slots(channel)


@router.get("/game-performance/{channel}")
async def get_game_performance(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    return await intel_repo.get_game_performance(channel)


# ---------------------------------------------------------------------------
# Weekly Reports
# ---------------------------------------------------------------------------

@router.get("/reports/{channel}")
async def list_reports(
    channel: str,
    limit: int = Query(default=12, le=52),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await intel_repo.list_weekly_reports(channel, limit)


@router.get("/reports/{channel}/{week_start}")
async def get_report(
    channel: str, week_start: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await intel_repo.get_weekly_report(channel, week_start)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result
