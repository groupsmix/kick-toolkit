"""Auto-Highlight Detection router."""

import logging

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_auth
from app.repositories import highlights as highlights_repo
from app.services.highlights import detect_hype_moments

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/highlights", tags=["highlights"])


@router.get("/summary/{channel}")
async def get_summary(
    channel: str,
    session_id: str | None = Query(default=None),
    _session: dict = Depends(require_auth),
) -> dict:
    return await highlights_repo.get_summary(channel, session_id=session_id)


@router.get("/list/{channel}")
async def get_highlights(
    channel: str,
    session_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await highlights_repo.get_highlights(channel, session_id=session_id, limit=limit)


@router.delete("/{highlight_id}")
async def delete_highlight(
    highlight_id: str, _session: dict = Depends(require_auth)
) -> dict:
    deleted = await highlights_repo.delete_highlight(highlight_id)
    if not deleted:
        return {"error": "Highlight not found"}
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Clip Highlighter Enhancements — Hype Detection
# ---------------------------------------------------------------------------

@router.post("/detect/{channel}")
async def detect_highlights(
    channel: str,
    session_id: str | None = Query(default=None),
    window_seconds: int = Query(default=60, ge=10, le=300),
    spike_threshold: float = Query(default=2.0, ge=1.0, le=5.0),
    _session: dict = Depends(require_auth),
) -> dict:
    """Analyze chat activity to detect highlight/hype moments via message rate spikes."""
    moments = await detect_hype_moments(
        channel=channel,
        session_id=session_id,
        window_seconds=window_seconds,
        spike_threshold=spike_threshold,
    )

    # Save detected moments as highlight markers
    saved = []
    for m in moments:
        hl = await highlights_repo.create_highlight(
            channel=channel,
            session_id=session_id,
            timestamp_offset_seconds=m["timestamp_offset_seconds"],
            intensity=m["intensity"],
            message_rate=m["message_rate"],
            duration_seconds=m["duration_seconds"],
            description=m["description"],
            sample_messages=m["sample_messages"],
            category=m["category"],
        )
        saved.append(hl)

    logger.info(
        "Detected %d hype moments for channel=%s session=%s",
        len(saved), channel, session_id,
    )
    return {
        "channel": channel,
        "session_id": session_id,
        "moments_detected": len(saved),
        "highlights": saved,
    }
