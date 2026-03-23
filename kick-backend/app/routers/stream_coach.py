"""AI Stream Coach router — real-time coaching suggestions for streamers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import (
    CoachAnalyzeRequest,
    CoachSettings,
    StreamSessionCreate,
)
from app.repositories import stream_coach as coach_repo
from app.services import stream_coach as coach_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coach", tags=["stream-coach"])


# ---------------------------------------------------------------------------
# Coach Settings
# ---------------------------------------------------------------------------

@router.get("/settings/{channel}")
async def get_coach_settings(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    return await coach_repo.get_settings(channel)


@router.put("/settings/{channel}")
async def update_coach_settings(
    channel: str, settings: CoachSettings, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    await coach_repo.upsert_settings(
        channel=channel,
        enabled=settings.enabled,
        engagement_alerts=settings.engagement_alerts,
        game_duration_alerts=settings.game_duration_alerts,
        viewer_change_alerts=settings.viewer_change_alerts,
        raid_welcome_alerts=settings.raid_welcome_alerts,
        sentiment_alerts=settings.sentiment_alerts,
        break_reminders=settings.break_reminders,
        break_reminder_minutes=settings.break_reminder_minutes,
        engagement_drop_threshold=settings.engagement_drop_threshold,
        viewer_change_threshold=settings.viewer_change_threshold,
    )
    logger.info("Coach settings updated for channel=%s", channel)
    return settings.model_dump()


# ---------------------------------------------------------------------------
# Stream Sessions
# ---------------------------------------------------------------------------

@router.post("/session/start")
async def start_session(
    body: StreamSessionCreate, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, body.channel)
    # End any existing active session first
    active = await coach_repo.get_active_session(body.channel)
    if active:
        await coach_repo.end_session(active["id"])

    coach_session = await coach_repo.create_session(body.channel, body.game)
    logger.info("Stream coaching session started for channel=%s", body.channel)
    return coach_session


@router.post("/session/{session_id}/end")
async def end_session(session_id: str, session: dict = Depends(require_auth)) -> dict:
    result = await coach_repo.end_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info("Stream coaching session ended: %s", session_id)
    return result


@router.get("/session/active/{channel}")
async def get_active_session(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    active = await coach_repo.get_active_session(channel)
    if not active:
        return {"session": None, "active": False}
    return {"session": active, "active": True}


@router.get("/session/{session_id}")
async def get_session(session_id: str, session: dict = Depends(require_auth)) -> dict:
    coach_session = await coach_repo.get_session(session_id)
    if not coach_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return coach_session


@router.get("/sessions/{channel}")
async def list_sessions(
    channel: str,
    limit: int = Query(default=10, le=50),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await coach_repo.list_sessions(channel, limit)


# ---------------------------------------------------------------------------
# Coaching Analysis & Suggestions
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_stream(
    body: CoachAnalyzeRequest, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, body.channel)
    result = await coach_service.analyze_stream(
        channel=body.channel,
        session_id=body.session_id,
        viewer_count=body.viewer_count,
        game=body.game,
    )
    return result


@router.get("/suggestions/{session_id}")
async def get_suggestions(
    session_id: str,
    include_dismissed: bool = False,
    session: dict = Depends(require_auth),
) -> list[dict]:
    return await coach_repo.get_suggestions(session_id, include_dismissed)


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str, session: dict = Depends(require_auth)
) -> dict:
    success = await coach_repo.dismiss_suggestion(suggestion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found or already dismissed")
    return {"status": "dismissed"}


@router.post("/suggestions/{session_id}/dismiss-all")
async def dismiss_all_suggestions(
    session_id: str, session: dict = Depends(require_auth)
) -> dict:
    count = await coach_repo.dismiss_all_suggestions(session_id)
    return {"status": "dismissed", "count": count}


# ---------------------------------------------------------------------------
# AI Insights
# ---------------------------------------------------------------------------

@router.get("/insights/{session_id}")
async def get_ai_insights(
    session_id: str, session: dict = Depends(require_auth)
) -> dict:
    coach_session = await coach_repo.get_session(session_id)
    if not coach_session:
        raise HTTPException(status_code=404, detail="Session not found")
    insights = await coach_service.get_ai_insights(coach_session["channel"], session_id)
    return {"insights": insights}


# ---------------------------------------------------------------------------
# Snapshots / Metrics
# ---------------------------------------------------------------------------

@router.get("/snapshots/{session_id}")
async def get_snapshots(
    session_id: str, session: dict = Depends(require_auth)
) -> list[dict]:
    return await coach_repo.get_snapshots(session_id)


@router.get("/chat-activity/{channel}")
async def get_chat_activity(
    channel: str,
    window_minutes: int = Query(default=30, le=120),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await coach_repo.get_chat_activity_trend(channel, window_minutes)
