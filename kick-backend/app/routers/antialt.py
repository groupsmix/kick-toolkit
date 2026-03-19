"""Anti-alt detection router."""

import random
from fastapi import APIRouter
from app.models.schemas import AltCheckRequest, AntiAltSettings
from app.services.database import anti_alt_settings, flagged_accounts, generate_id, now_iso

router = APIRouter(prefix="/api/antialt", tags=["antialt"])


@router.post("/check")
async def check_user(req: AltCheckRequest) -> dict:
    """Simulate alt account detection analysis."""
    username = req.username.lower()

    existing = next((a for a in flagged_accounts if a["username"].lower() == username), None)
    if existing:
        return existing

    flags = []
    risk_score = 0.0

    # Simulate account age check
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

    # Simulate follower check
    fake_followers = random.randint(0, 500)
    if fake_followers == 0:
        flags.append("No followers")
        risk_score += 20
    elif fake_followers < 5:
        flags.append("Low follower count")
        risk_score += 10

    # Name pattern check
    sus_patterns = ["xx", "alt", "new", "temp", "fake", "bot", "spam", "test"]
    if any(p in username for p in sus_patterns):
        flags.append("Username pattern match")
        risk_score += 15

    # Random additional flags for demo
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

    result = {
        "username": req.username,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "account_age_days": fake_age,
        "follower_count": fake_followers,
        "is_following": random.choice([True, False]),
        "similar_names": [],
        "created_at": now_iso(),
    }

    if risk_score >= anti_alt_settings.get("auto_timeout_threshold", 50):
        flagged_accounts.append(result)

    return result


@router.get("/flagged")
async def get_flagged() -> list[dict]:
    return sorted(flagged_accounts, key=lambda x: x["risk_score"], reverse=True)


@router.get("/settings")
async def get_settings() -> dict:
    return anti_alt_settings


@router.put("/settings")
async def update_settings(settings: AntiAltSettings) -> dict:
    anti_alt_settings.update(settings.model_dump())
    return anti_alt_settings


@router.delete("/flagged/{username}")
async def remove_flagged(username: str) -> dict:
    global flagged_accounts
    flagged_accounts[:] = [a for a in flagged_accounts if a["username"].lower() != username.lower()]
    return {"status": "removed"}


@router.post("/whitelist/{username}")
async def whitelist_user(username: str) -> dict:
    if username not in anti_alt_settings["whitelisted_users"]:
        anti_alt_settings["whitelisted_users"].append(username)
    flagged_accounts[:] = [a for a in flagged_accounts if a["username"].lower() != username.lower()]
    return {"status": "whitelisted", "user": username}
