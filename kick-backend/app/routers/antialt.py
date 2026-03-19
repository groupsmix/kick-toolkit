"""Anti-alt detection router."""

import json
import random

from fastapi import APIRouter, Depends

from app.dependencies import require_auth
from app.models.schemas import AltCheckRequest, AntiAltSettings
from app.services.db import get_conn, _now_iso

router = APIRouter(prefix="/api/antialt", tags=["antialt"])


@router.post("/check")
async def check_user(req: AltCheckRequest, _session: dict = Depends(require_auth)) -> dict:
    """Simulate alt account detection analysis."""
    username = req.username.lower()

    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM flagged_accounts WHERE lower(username) = lower(%s)", (username,)
        )
        existing = await row.fetchone()

    if existing:
        return dict(existing)

    flags = []
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
    now = _now_iso()

    result = {
        "username": req.username,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "account_age_days": fake_age,
        "follower_count": fake_followers,
        "is_following": is_following,
        "similar_names": [],
        "created_at": now,
    }

    # Get threshold from settings
    async with get_conn() as conn:
        row = await conn.execute("SELECT auto_timeout_threshold FROM anti_alt_settings WHERE id = 1")
        settings = await row.fetchone()
        threshold = settings["auto_timeout_threshold"] if settings else 50.0

        if risk_score >= threshold:
            await conn.execute(
                """INSERT INTO flagged_accounts (username, risk_score, risk_level, flags, account_age_days,
                   follower_count, is_following, similar_names, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (username) DO UPDATE SET risk_score = EXCLUDED.risk_score""",
                (req.username, risk_score, risk_level, json.dumps(flags), fake_age,
                 fake_followers, is_following, "[]", now),
            )
            await conn.commit()

    return result


@router.get("/flagged")
async def get_flagged(_session: dict = Depends(require_auth)) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM flagged_accounts ORDER BY risk_score DESC")
        accounts = await row.fetchall()
    return [dict(a) for a in accounts]


@router.get("/settings")
async def get_settings(_session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM anti_alt_settings WHERE id = 1")
        settings = await row.fetchone()
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
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO anti_alt_settings (id, enabled, min_account_age_days, auto_ban_threshold,
               auto_timeout_threshold, check_name_similarity, check_follow_status, whitelisted_users)
               VALUES (1, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
                   enabled = EXCLUDED.enabled, min_account_age_days = EXCLUDED.min_account_age_days,
                   auto_ban_threshold = EXCLUDED.auto_ban_threshold,
                   auto_timeout_threshold = EXCLUDED.auto_timeout_threshold,
                   check_name_similarity = EXCLUDED.check_name_similarity,
                   check_follow_status = EXCLUDED.check_follow_status,
                   whitelisted_users = EXCLUDED.whitelisted_users""",
            (settings.enabled, settings.min_account_age_days, settings.auto_ban_threshold,
             settings.auto_timeout_threshold, settings.check_name_similarity,
             settings.check_follow_status, json.dumps(settings.whitelisted_users)),
        )
        await conn.commit()
    return settings.model_dump()


@router.delete("/flagged/{username}")
async def remove_flagged(username: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM flagged_accounts WHERE lower(username) = lower(%s)", (username,))
        await conn.commit()
    return {"status": "removed"}


@router.post("/whitelist/{username}")
async def whitelist_user(username: str, _session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT whitelisted_users FROM anti_alt_settings WHERE id = 1")
        settings = await row.fetchone()
        if settings:
            wl = settings["whitelisted_users"] if isinstance(settings["whitelisted_users"], list) else json.loads(settings["whitelisted_users"])
            if username not in wl:
                wl.append(username)
                await conn.execute(
                    "UPDATE anti_alt_settings SET whitelisted_users = %s WHERE id = 1",
                    (json.dumps(wl),),
                )
        await conn.execute("DELETE FROM flagged_accounts WHERE lower(username) = lower(%s)", (username,))
        await conn.commit()
    return {"status": "whitelisted", "user": username}
