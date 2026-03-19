"""Anti-alt detection router."""

import logging
import random

from fastapi import APIRouter, Depends

from app.dependencies import require_auth
from app.models.schemas import AltCheckRequest, AntiAltSettings
from app.repositories import antialt as antialt_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/antialt", tags=["antialt"])


@router.post("/check")
async def check_user(req: AltCheckRequest, _session: dict = Depends(require_auth)) -> dict:
    """Simulate alt account detection analysis."""
    username = req.username.lower()

    existing = await antialt_repo.get_flagged_account(username)
    if existing:
        return existing

    flags: list[str] = []
    risk_score = 0.0

    fake_age = random.randint(0, 365)
    if fake_age < 1:
        flags.append("Account age < 1 day")
        risk_score += 30
    elif fake_age < 7:
        flags.append("Account age < 7 days")
        risk_score += 20
    elif fake_age < 30:
        flags.append("Account age < 30 days")
        risk_score += 10

    fake_followers = random.randint(0, 500)
    if fake_followers == 0:
        flags.append("No followers")
        risk_score += 20
    elif fake_followers < 5:
        flags.append("Low follower count")
        risk_score += 10

    sus_patterns = ["xx", "alt", "new", "temp", "fake", "bot", "spam", "test"]
    if any(p in username for p in sus_patterns):
        flags.append("Username pattern match")
        risk_score += 15

    if random.random() > 0.7:
        flags.append("Low engagement")
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

    is_following = random.choice([True, False])

    result = {
        "username": req.username,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "account_age_days": fake_age,
        "follower_count": fake_followers,
        "is_following": is_following,
        "similar_names": [],
    }

    threshold = await antialt_repo.get_timeout_threshold()
    if risk_score >= threshold:
        await antialt_repo.insert_flagged_account(
            req.username, risk_score, risk_level, flags,
            fake_age, fake_followers, is_following,
        )
        logger.info("User %s flagged with risk_score=%.1f", req.username, risk_score)

    return result


@router.get("/flagged")
async def get_flagged(_session: dict = Depends(require_auth)) -> list[dict]:
    return await antialt_repo.list_flagged()


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
