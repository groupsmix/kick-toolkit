"""AI Clip-to-TikTok Pipeline router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import ClipCreate, ClipPostRequest, ClipCaptionRequest
from app.repositories import clips as clips_repo
from app.services import clips as clips_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clips", tags=["clips"])


# ---------------------------------------------------------------------------
# Hype Moments
# ---------------------------------------------------------------------------

@router.get("/hype-moments/{channel}")
async def get_hype_moments(
    channel: str,
    limit: int = Query(default=20, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await clips_repo.get_hype_moments(channel, limit)


@router.post("/hype-moments/detect/{channel}")
async def detect_hype_moments(
    channel: str,
    window_minutes: int = Query(default=60, le=1440),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    moments = await clips_service.detect_hype_moments(channel, window_minutes)
    logger.info("Detected %d hype moments for channel=%s", len(moments), channel)
    return moments


# ---------------------------------------------------------------------------
# Clips
# ---------------------------------------------------------------------------

@router.post("/generate")
async def create_clip(
    body: ClipCreate, _session: dict = Depends(require_auth)
) -> dict:
    clip = await clips_repo.create_clip(
        channel=body.channel,
        hype_moment_id=body.hype_moment_id,
        title=body.title,
        description=body.description,
        duration_seconds=body.duration_seconds,
    )
    # Mark the hype moment as used if provided
    if body.hype_moment_id:
        await clips_repo.update_hype_moment_status(body.hype_moment_id, "clipped")
    logger.info("Clip created id=%s for channel=%s", clip["id"], body.channel)
    return clip


@router.get("/list/{channel}")
async def list_clips(
    channel: str,
    limit: int = Query(default=20, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    return await clips_repo.list_clips(channel, limit)


@router.get("/{clip_id}")
async def get_clip(
    clip_id: str, _session: dict = Depends(require_auth)
) -> dict:
    clip = await clips_repo.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.delete("/{clip_id}")
async def delete_clip(
    clip_id: str, _session: dict = Depends(require_auth)
) -> dict:
    deleted = await clips_repo.delete_clip(clip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Caption Generation
# ---------------------------------------------------------------------------

@router.post("/{clip_id}/caption")
async def generate_caption(
    clip_id: str,
    body: ClipCaptionRequest,
    _session: dict = Depends(require_auth),
) -> dict:
    clip = await clips_repo.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    caption = await clips_service.generate_caption(clip_id, body.style)
    return {"caption": caption}


# ---------------------------------------------------------------------------
# Social Posting
# ---------------------------------------------------------------------------

@router.post("/{clip_id}/post")
async def post_clip(
    clip_id: str,
    body: ClipPostRequest,
    _session: dict = Depends(require_auth),
) -> dict:
    clip = await clips_repo.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    if body.platform not in ("tiktok", "youtube", "instagram"):
        raise HTTPException(status_code=400, detail="Platform must be tiktok, youtube, or instagram")
    return await clips_service.post_to_platform(clip_id, body.platform, body.caption)


@router.get("/{clip_id}/posts")
async def get_clip_posts(
    clip_id: str, _session: dict = Depends(require_auth)
) -> list[dict]:
    return await clips_repo.get_clip_posts(clip_id)
