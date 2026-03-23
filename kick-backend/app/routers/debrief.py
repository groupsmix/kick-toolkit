"""AI Post-Stream Debrief router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import DebriefRequest
from app.repositories import debrief as debrief_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debrief", tags=["debrief"])


@router.get("/list/{channel}")
async def get_debriefs(
    channel: str,
    limit: int = Query(default=10, le=50),
    session: dict = Depends(require_auth),
) -> list[dict]:
    require_channel_owner(session, channel)
    return await debrief_repo.get_debriefs(channel, limit)


@router.get("/detail/{debrief_id}")
async def get_debrief(debrief_id: str, _session: dict = Depends(require_auth)) -> dict:
    result = await debrief_repo.get_debrief(debrief_id)
    if not result:
        return {"error": "Debrief not found"}
    return result


@router.get("/session/{channel}/{session_id}")
async def get_debrief_by_session(
    channel: str, session_id: str, session: dict = Depends(require_auth)
) -> dict:
    require_channel_owner(session, channel)
    result = await debrief_repo.get_debrief_by_session(channel, session_id)
    if not result:
        return {"error": "No debrief found for this session"}
    return result


@router.post("/generate")
async def generate_debrief(
    body: DebriefRequest, session: dict = Depends(require_auth)
) -> dict:
    """Generate a post-stream debrief. In production this would call OpenAI."""
    require_channel_owner(session, body.channel)
    result = await debrief_repo.create_debrief(
        channel=body.channel,
        session_id=body.session_id,
        summary="AI-generated debrief analysis. Connect OpenAI API key to enable full analysis.",
        top_moments=[],
        sentiment_timeline=[],
        chat_highlights=[],
        recommendations=[
            "Connect your OpenAI API key in settings to enable AI-powered stream analysis",
            "Once connected, debriefs will analyze chat sentiment, detect top moments, and provide actionable insights",
        ],
        title_suggestions=[],
        trending_topics=[],
    )
    logger.info("Debrief generated for channel=%s session=%s", body.channel, body.session_id)
    return result
