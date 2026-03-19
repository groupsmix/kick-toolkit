"""AI Post-Stream Debrief router — AI-powered stream analysis and insights."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import DebriefRequest
from app.repositories import debrief as debrief_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debrief", tags=["debrief"])


@router.post("/")
async def create_debrief(
    body: DebriefRequest, _session: dict = Depends(require_auth)
) -> dict:
    result = await debrief_repo.create_debrief(
        channel=body.channel,
        stream_date=body.stream_date or "",
        session_id=body.session_id,
    )
    logger.info("Debrief created for channel=%s", body.channel)
    return result


@router.get("/list/{channel}")
async def list_debriefs(
    channel: str,
    limit: int = Query(default=20, le=100),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await debrief_repo.list_debriefs(channel, limit)


@router.get("/{debrief_id}")
async def get_debrief(debrief_id: str, _session: dict = Depends(require_auth)) -> dict:
    result = await debrief_repo.get_debrief(debrief_id)
    if not result:
        raise HTTPException(status_code=404, detail="Debrief not found")
    return result


@router.get("/session/{session_id}")
async def get_debrief_by_session(
    session_id: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await debrief_repo.get_debrief_by_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="No debrief found for this session")
    return result


@router.delete("/{debrief_id}")
async def delete_debrief(debrief_id: str, _session: dict = Depends(require_auth)) -> dict:
    await debrief_repo.delete_debrief(debrief_id)
    return {"status": "deleted"}
