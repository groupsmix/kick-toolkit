"""Auto-verification pipeline for new users on first chat message."""

import logging
from typing import Optional

from app.services.db import get_conn, _now_iso
from app.services import fingerprint as fp_svc
from app.services import behavior_analysis as behavior_svc
from app.services import challenge as challenge_svc
from app.services import name_similarity as name_svc
from app.services.risk_scoring import (
    risk_engine,
    calculate_account_age_score,
    calculate_follower_score,
)

logger = logging.getLogger(__name__)


async def _get_banned_usernames(channel: str) -> list[str]:
    """Get list of banned usernames for a channel."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT username FROM banned_users WHERE channel = %s",
            (channel,),
        )
        rows = await row.fetchall()
    return [r["username"] for r in rows]


async def _is_whitelisted(username: str, channel: str) -> bool:
    """Check if a user is whitelisted."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT 1 FROM whitelisted_users WHERE lower(username) = lower(%s) AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return result is not None


async def _get_settings() -> dict:
    """Get anti-alt settings."""
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM anti_alt_settings WHERE id = 1")
        result = await row.fetchone()
    if result:
        return dict(result)
    return {
        "enabled": True,
        "min_account_age_days": 7,
        "auto_ban_threshold": 80.0,
        "auto_timeout_threshold": 50.0,
        "check_name_similarity": True,
        "check_follow_status": True,
        "challenge_enabled": False,
        "challenge_type": "follow",
        "challenge_wait_minutes": 10,
        "challenge_message": "Please follow the channel and wait {minutes} minutes before chatting.",
    }


async def _is_first_message(username: str, channel: str) -> bool:
    """Check if this is the user's first message in the channel."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT count(*) as cnt FROM chat_logs WHERE lower(username) = lower(%s) AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return (result["cnt"] if result else 0) <= 1


async def auto_verify(
    username: str,
    channel: str,
    message: str,
    account_age_days: int = 0,
    follower_count: int = 0,
    is_following: bool = False,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    fingerprint_data: Optional[str] = None,
) -> dict:
    """Run the full auto-verification pipeline.

    Returns dict with keys: action, risk_score, flags, challenge_type, challenge_message
    """
    settings = await _get_settings()

    if not settings.get("enabled", True):
        return {"action": "allow", "risk_score": 0.0, "flags": []}

    # Check whitelist first
    if await _is_whitelisted(username, channel):
        return {"action": "allow", "risk_score": 0.0, "flags": ["Whitelisted user"]}

    # Check if there's a pending challenge
    existing_challenge = await challenge_svc.check_challenge(username, channel)
    if existing_challenge and existing_challenge["challenge_status"] == "pending":
        return {
            "action": "challenge",
            "risk_score": 0.0,
            "flags": ["Pending challenge"],
            "challenge_type": existing_challenge["challenge_type"],
            "challenge_message": settings.get("challenge_message", ""),
        }

    flags: list[str] = []
    features: dict[str, float] = {}

    # 1. Account age check
    features["account_age_score"] = calculate_account_age_score(account_age_days)
    if account_age_days < 1:
        flags.append("Account age < 1 day")
    elif account_age_days < 7:
        flags.append("Account age < 7 days")
    elif account_age_days < 30:
        flags.append("Account age < 30 days")

    # 2. Follower score
    features["follower_score"] = calculate_follower_score(follower_count)
    if follower_count == 0:
        flags.append("No followers")
    elif follower_count < 5:
        flags.append("Low follower count")

    # 3. Follow status
    features["follow_status_score"] = 0.0 if is_following else 0.5
    if not is_following:
        flags.append("Not following channel")

    # 4. Username pattern matching
    pattern_flags = name_svc.get_pattern_flags(username)
    flags.extend(pattern_flags)
    features["pattern_score"] = 1.0 if pattern_flags else 0.0

    # 5. Name similarity against banned users
    banned_names = await _get_banned_usernames(channel)
    if banned_names and settings.get("check_name_similarity", True):
        similar = name_svc.find_similar_names(username, banned_names)
        if similar:
            top_name, top_score = similar[0]
            features["name_similarity_score"] = top_score
            flags.append(f"Name similar to banned user '{top_name}' ({top_score:.0%})")
        else:
            features["name_similarity_score"] = 0.0
    else:
        features["name_similarity_score"] = 0.0

    # 6. Fingerprint check
    if client_ip or user_agent:
        await fp_svc.record_fingerprint(username, channel, client_ip, user_agent)
    fp_score, fp_matches = await fp_svc.get_fingerprint_risk_score(
        username, channel, banned_names,
    )
    features["fingerprint_score"] = fp_score / 25.0  # Normalize to 0-1
    if fp_matches:
        flags.append(f"Fingerprint matches banned users: {', '.join(fp_matches[:3])}")

    # 7. Behavior similarity
    if banned_names:
        similar_profiles = await behavior_svc.find_similar_banned_profiles(
            username, channel, banned_names,
        )
        if similar_profiles:
            top_name, top_sim = similar_profiles[0]
            features["behavior_similarity_score"] = top_sim
            flags.append(f"Behavior similar to banned user '{top_name}' ({top_sim:.0%})")
        else:
            features["behavior_similarity_score"] = 0.0
    else:
        features["behavior_similarity_score"] = 0.0

    # 8. Chat history score (new users with no history are more suspicious)
    first_msg = await _is_first_message(username, channel)
    features["chat_history_score"] = 0.8 if first_msg else 0.0
    if first_msg:
        flags.append("First message in channel")

    # Calculate risk using ML engine
    risk_score = await risk_engine.calculate_risk(channel, features)

    # Update behavior profile with this message
    await behavior_svc.update_profile(username, channel, message)

    # Determine action
    auto_ban = settings.get("auto_ban_threshold", 80.0)
    auto_timeout = settings.get("auto_timeout_threshold", 50.0)

    if risk_score >= auto_ban:
        action = "ban"
    elif risk_score >= auto_timeout:
        action = "timeout"
    elif (
        settings.get("challenge_enabled", False)
        and first_msg
        and risk_score >= 25
    ):
        # Create a challenge for moderately suspicious first-time chatters
        challenge_type = settings.get("challenge_type", "follow")
        wait_minutes = settings.get("challenge_wait_minutes", 10)
        await challenge_svc.create_challenge(username, channel, challenge_type, wait_minutes)
        action = "challenge"
    else:
        action = "allow"

    # Record action for ML training
    await risk_engine.record_action(
        username, channel, action, risk_score, features, "system",
    )

    # Flag the account if above timeout threshold
    if risk_score >= auto_timeout:
        risk_level = "critical" if risk_score >= 80 else "high"
        await _store_flagged_account(
            username, risk_score, risk_level, flags,
            account_age_days, follower_count, is_following,
            len(fp_matches), features.get("behavior_similarity_score", 0.0),
        )

    result: dict = {
        "action": action,
        "risk_score": risk_score,
        "flags": flags,
    }

    if action == "challenge":
        result["challenge_type"] = settings.get("challenge_type", "follow")
        result["challenge_message"] = settings.get(
            "challenge_message", ""
        ).replace("{minutes}", str(settings.get("challenge_wait_minutes", 10)))

    return result


async def _store_flagged_account(
    username: str,
    risk_score: float,
    risk_level: str,
    flags: list[str],
    account_age_days: int,
    follower_count: int,
    is_following: bool,
    fingerprint_match_count: int,
    behavior_similarity_score: float,
) -> None:
    """Store a flagged account in the database."""
    import json
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO flagged_accounts
               (username, risk_score, risk_level, flags, account_age_days,
                follower_count, is_following, similar_names, fingerprint_match_count,
                behavior_similarity_score, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (username) DO UPDATE SET
                   risk_score = EXCLUDED.risk_score,
                   risk_level = EXCLUDED.risk_level,
                   flags = EXCLUDED.flags,
                   fingerprint_match_count = EXCLUDED.fingerprint_match_count,
                   behavior_similarity_score = EXCLUDED.behavior_similarity_score""",
            (username, risk_score, risk_level, json.dumps(flags),
             account_age_days, follower_count, is_following, "[]",
             fingerprint_match_count, behavior_similarity_score, now),
        )
        await conn.commit()
