"""Anti-alt detection router (enhanced)."""

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import (
    AltCheckRequest,
    AltCheckResult,
    AntiAltSettings,
    AutoVerifyRequest,
    AutoVerifyResult,
    BannedUser,
    ChallengeCheck,
    ChallengeResult,
    RiskModelStats,
    WhitelistedUser,
)
from app.repositories import antialt as antialt_repo
from app.repositories import banned as banned_repo
from app.repositories import whitelist as whitelist_repo
from app.services import auto_verify as verify_svc
from app.services import behavior_analysis as behavior_svc
from app.services import challenge as challenge_svc
from app.services import name_similarity as name_svc
from app.services.kick_auth import decrypt_token
from app.services.risk_scoring import risk_engine

KICK_API_BASE = "https://api.kick.com/public/v1"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/antialt", tags=["antialt"])

_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _http_client


async def close_http_client() -> None:
    """Close the module-level HTTP client, releasing TCP connections."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


async def _fetch_kick_user_data(
    username: str, access_token: str,
) -> tuple[int, int, bool]:
    """Fetch real account data from Kick API.

    Returns (account_age_days, follower_count, is_following).
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    client = _get_http_client()
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
async def check_user(req: AltCheckRequest, session: dict = Depends(require_auth)) -> AltCheckResult:
    """Analyze a user for alt account indicators using real Kick API data."""
    require_channel_owner(session, req.channel)
    username = req.username.lower()

    existing = await antialt_repo.get_flagged_account(username)
    if existing:
        return AltCheckResult(**existing)

    raw_token = session.get("access_token", "")
    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="No Kick access token available. Please re-authenticate.",
        )
    access_token = decrypt_token(raw_token)

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

    # Enhanced name similarity check
    banned_names = await banned_repo.get_banned_usernames(req.channel)
    similar_names: list[str] = []
    if banned_names:
        similar = name_svc.find_similar_names(username, banned_names)
        for name, score in similar[:5]:
            similar_names.append(name)
            flags.append(f"Name similar to banned '{name}' ({score:.0%})")
            risk_score += 15 * score

    # Pattern check
    pattern_flags = name_svc.get_pattern_flags(username)
    flags.extend(pattern_flags)
    if pattern_flags:
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
        similar_names=similar_names,
    )


@router.get("/flagged")
async def get_flagged(channel: str, session: dict = Depends(require_auth)) -> list[AltCheckResult]:
    require_channel_owner(session, channel)
    rows = await antialt_repo.list_flagged()
    return [AltCheckResult(**row) for row in rows]


@router.get("/settings")
async def get_settings(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    settings = await antialt_repo.get_settings()
    if not settings:
        return AntiAltSettings().model_dump()
    result = dict(settings)
    result.pop("id", None)
    return result


@router.put("/settings")
async def update_settings(settings: AntiAltSettings, channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await antialt_repo.upsert_settings(settings)
    logger.info("Anti-alt settings updated by channel=%s", channel)
    return settings.model_dump()


@router.delete("/flagged/{username}")
async def remove_flagged(username: str, channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await antialt_repo.remove_flagged(username)
    logger.info("User %s removed from flagged list", username)
    return {"status": "removed"}


# ========== Auto-Verify ==========


@router.post("/auto-verify")
async def auto_verify_user(
    req: AutoVerifyRequest,
    session: dict = Depends(require_auth),
) -> AutoVerifyResult:
    """Auto-verify a user on first chat message."""
    require_channel_owner(session, req.channel)
    raw_token = session.get("access_token", "")
    access_token = decrypt_token(raw_token) if raw_token else ""

    account_age_days = 0
    follower_count = 0
    is_following = False
    if access_token:
        try:
            account_age_days, follower_count, is_following = await _fetch_kick_user_data(
                req.username, access_token,
            )
        except Exception:
            logger.warning("Failed to fetch Kick data for %s", req.username)

    result = await verify_svc.auto_verify(
        username=req.username,
        channel=req.channel,
        message=req.message,
        account_age_days=account_age_days,
        follower_count=follower_count,
        is_following=is_following,
        client_ip=req.client_ip,
        user_agent=req.user_agent,
        fingerprint_data=req.fingerprint,
    )

    return AutoVerifyResult(
        action=result["action"],
        risk_score=result["risk_score"],
        flags=result.get("flags", []),
        challenge_type=result.get("challenge_type"),
        challenge_message=result.get("challenge_message"),
    )


# ========== Banned Users ==========


@router.get("/banned-users")
async def list_banned_users(channel: str, session: dict = Depends(require_auth)) -> list[BannedUser]:
    require_channel_owner(session, channel)
    rows = await banned_repo.list_banned(channel)
    return [BannedUser(**r) for r in rows]


@router.post("/banned-users")
async def add_banned_user(user: BannedUser, session: dict = Depends(require_auth)) -> BannedUser:
    require_channel_owner(session, user.channel)
    result = await banned_repo.add_banned(
        user.username, user.channel, user.ban_reason or "", user.ban_source,
    )
    logger.info("User %s added to ban list for channel=%s", user.username, user.channel)
    return BannedUser(**result)


@router.delete("/banned-users/{username}")
async def remove_banned_user(username: str, channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    await banned_repo.remove_banned(username, channel)
    logger.info("User %s removed from ban list", username)
    return {"status": "removed"}


# ========== Whitelist ==========


@router.get("/whitelist")
async def list_whitelisted(channel: str, session: dict = Depends(require_auth)) -> list[WhitelistedUser]:
    require_channel_owner(session, channel)
    rows = await whitelist_repo.list_whitelisted(channel)
    return [WhitelistedUser(**r) for r in rows]


@router.post("/whitelist/{username}")
async def whitelist_user(
    username: str,
    channel: str,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    await whitelist_repo.add_whitelisted(username, channel, added_by="streamer", reason="Manual whitelist")
    await antialt_repo.whitelist_user(username)
    logger.info("User %s whitelisted", username)
    return {"status": "whitelisted", "user": username}


@router.delete("/whitelist/{username}")
async def remove_whitelisted(
    username: str,
    channel: str,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    await whitelist_repo.remove_whitelisted(username, channel)
    logger.info("User %s removed from whitelist", username)
    return {"status": "removed"}


# ========== Challenges ==========


@router.post("/challenge/check")
async def check_challenge(req: ChallengeCheck, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, req.channel)
    result = await challenge_svc.check_challenge(req.username, req.channel)
    if not result:
        return {"status": "no_challenge", "completed": True}
    return result


@router.post("/challenge/verify")
async def verify_challenge(req: ChallengeCheck, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, req.channel)
    raw_token = session.get("access_token", "")
    access_token = decrypt_token(raw_token) if raw_token else ""
    is_following = False
    if access_token:
        try:
            _, _, is_following = await _fetch_kick_user_data(req.username, access_token)
        except Exception:
            pass

    result = await challenge_svc.verify_challenge(req.username, req.channel, is_following)
    return result


@router.get("/challenges")
async def list_challenges(channel: str, session: dict = Depends(require_auth)) -> list[ChallengeResult]:
    require_channel_owner(session, channel)
    rows = await challenge_svc.list_active_challenges(channel)
    return [ChallengeResult(**r) for r in rows]


# ========== Behavior Profiles ==========


@router.get("/behavior/{username}")
async def get_behavior_profile(
    username: str,
    channel: str,
    session: dict = Depends(require_auth),
) -> dict:
    require_channel_owner(session, channel)
    profile = await behavior_svc.get_profile(username, channel)
    if not profile:
        return {"username": username, "channel": channel, "message_count": 0}
    return profile


# ========== Risk Model ==========


@router.get("/risk-model/stats")
async def get_risk_model_stats(channel: str, session: dict = Depends(require_auth)) -> RiskModelStats:
    require_channel_owner(session, channel)
    stats = await risk_engine.get_model_stats(channel)
    return RiskModelStats(**stats)


@router.post("/risk-model/retrain")
async def retrain_risk_model(channel: str, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, channel)
    result = await risk_engine.retrain(channel)
    logger.info("Risk model retrain requested for channel=%s: %s", channel, result.get("status"))
    return result
