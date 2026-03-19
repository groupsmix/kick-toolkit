"""Anti-alt detection router."""

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import AltCheckRequest, AltCheckResult, AntiAltSettings
from app.repositories import antialt as antialt_repo

KICK_API_BASE = "https://api.kick.com/public/v1"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/antialt", tags=["antialt"])


async def _fetch_kick_user_data(
    username: str, access_token: str,
) -> tuple[int, int, bool]:
    """Fetch real account data from Kick API.

    Returns (account_age_days, follower_count, is_following).
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get channel info by slug to retrieve follower count and creation date
        channel_resp = await client.get(
            f"{KICK_API_BASE}/channels",
            params={"slug": username},
            headers=headers,
        )

        account_age_days = 0
        follower_count = 0
        is_following = False

        if channel_resp.status_code == 200:
            channel_data = channel_resp.json()
            channels = channel_data.get("data", [])
            if channels:
                channel = channels[0] if isinstance(channels, list) else channels
                follower_count = channel.get("followers_count", 0)

                created_at = channel.get("created_at")
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        account_age_days = (datetime.now(timezone.utc) - created_dt).days
                    except (ValueError, TypeError):
                        pass

                is_following = channel.get("is_following", False)

    return account_age_days, follower_count, is_following


@router.post("/check")
async def check_user(req: AltCheckRequest, _session: dict = Depends(require_auth)) -> AltCheckResult:
    """Analyze a user for alt account indicators using real Kick API data."""
    username = req.username.lower()

    existing = await antialt_repo.get_flagged_account(username)
    if existing:
        return AltCheckResult(**existing)

    access_token = _session.get("access_token", "")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No Kick access token available. Please re-authenticate.",
        )

    account_age_days, follower_count, is_following = await _fetch_kick_user_data(
        username, access_token,
    )

    flags: list[str] = []
    risk_score = 0.0

    if account_age_days < 1:
        flags.append("Account age < 1 day")
        risk_score += 30
    elif account_age_days < 7:
        flags.append("Account age < 7 days")
        risk_score += 20
    elif account_age_days < 30:
        flags.append("Account age < 30 days")
        risk_score += 10

    if follower_count == 0:
        flags.append("No followers")
        risk_score += 20
    elif follower_count < 5:
        flags.append("Low follower count")
        risk_score += 10

    sus_patterns = ["xx", "alt", "new", "temp", "fake", "bot", "spam", "test"]
    if any(p in username for p in sus_patterns):
        flags.append("Username pattern match")
        risk_score += 15

    if not is_following:
        flags.append("Not following channel")
        risk_score += 10

    risk_score = min(risk_score, 100)

    if risk_score >= 80:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    threshold = await antialt_repo.get_timeout_threshold()
    if risk_score >= threshold:
        await antialt_repo.insert_flagged_account(
            req.username, risk_score, risk_level, flags,
            account_age_days, follower_count, is_following,
        )
        logger.info("User %s flagged with risk_score=%.1f", req.username, risk_score)

    return AltCheckResult(
        username=req.username,
        risk_score=risk_score,
        risk_level=risk_level,
        flags=flags,
        account_age_days=account_age_days,
        follower_count=follower_count,
        is_following=is_following,
        similar_names=[],
    )


@router.get("/flagged")
async def get_flagged(_session: dict = Depends(require_auth)) -> list[AltCheckResult]:
    rows = await antialt_repo.list_flagged()
    return [AltCheckResult(**row) for row in rows]


@router.get("/settings")
async def get_settings(_session: dict = Depends(require_auth)) -> dict:
    settings = await antialt_repo.get_settings()
    if not settings:
        return {
            "enabled": True, "min_account_age_days": 7, "auto_ban_threshold": 80.0,
            "auto_timeout_threshold": 50.0, "check_name_similarity": True,
            "check_follow_status": True, "whitelisted_users": [],
        }
    result = dict(settings)
    result.pop("id", None)
    return result


@router.put("/settings")
async def update_settings(settings: AntiAltSettings, _session: dict = Depends(require_auth)) -> dict:
    await antialt_repo.upsert_settings(
        settings.enabled, settings.min_account_age_days, settings.auto_ban_threshold,
        settings.auto_timeout_threshold, settings.check_name_similarity,
        settings.check_follow_status, settings.whitelisted_users,
    )
    logger.info("Anti-alt settings updated")
    return settings.model_dump()


@router.delete("/flagged/{username}")
async def remove_flagged(username: str, _session: dict = Depends(require_auth)) -> dict:
    await antialt_repo.remove_flagged(username)
    logger.info("User %s removed from flagged list", username)
    return {"status": "removed"}


@router.post("/whitelist/{username}")
async def whitelist_user(username: str, _session: dict = Depends(require_auth)) -> dict:
    await antialt_repo.whitelist_user(username)
    logger.info("User %s whitelisted", username)
    return {"status": "whitelisted", "user": username}
