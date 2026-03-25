"""Public Streamer Profile router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, safe_json_parse
from app.models.schemas import StreamerProfileUpdate
from app.repositories import profiles as profiles_repo
from app.repositories import schedule as schedule_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("/me")
async def get_my_profile(session: dict = Depends(require_auth)) -> dict:
    user_data = safe_json_parse(session.get("user_data", {}))
    channel = user_data.get("streamer_channel") or user_data.get("name", "")
    profile = await profiles_repo.get_profile(channel)
    if profile:
        return profile
    return {
        "channel": channel, "display_name": user_data.get("name", ""),
        "bio": "", "avatar_url": user_data.get("profile_picture"),
        "banner_url": None, "social_links": {}, "is_public": True,
        "theme_color": "#10b981", "total_followers": 0,
    }


@router.put("/me")
async def update_my_profile(
    body: StreamerProfileUpdate, session: dict = Depends(require_auth)
) -> dict:
    user_data = safe_json_parse(session.get("user_data", {}))
    channel = user_data.get("streamer_channel") or user_data.get("name", "")

    # Get existing or defaults
    existing = await profiles_repo.get_profile(channel)
    if existing:
        updates = body.model_dump(exclude_none=True)
        result = await profiles_repo.update_profile(channel, **updates) or existing
    else:
        result = await profiles_repo.upsert_profile(
            channel=channel,
            display_name=body.display_name or user_data.get("name", ""),
            bio=body.bio or "",
            avatar_url=body.avatar_url or user_data.get("profile_picture"),
            banner_url=body.banner_url,
            social_links=body.social_links or {},
            is_public=body.is_public if body.is_public is not None else True,
            theme_color=body.theme_color or "#10b981",
        )
    logger.info("Profile updated for channel=%s", channel)
    return result


# Public endpoint (no auth required)
@router.get("/public/{channel}")
async def get_public_profile(channel: str) -> dict:
    profile = await profiles_repo.get_public_profile(channel)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    schedule = await schedule_repo.get_public_schedule(channel)
    return {"profile": profile, "schedule": schedule}
