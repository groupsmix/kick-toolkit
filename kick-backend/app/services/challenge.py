"""Challenge/gate system for new account verification."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.db import get_conn, _now_iso

logger = logging.getLogger(__name__)


async def create_challenge(
    username: str,
    channel: str,
    challenge_type: str,
    wait_minutes: int = 10,
) -> dict:
    """Create a new challenge for a user."""
    now = _now_iso()
    expires_at = None
    if challenge_type == "wait":
        expires = datetime.now(timezone.utc) + timedelta(minutes=wait_minutes)
        expires_at = expires.isoformat()

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO user_challenges (username, channel, challenge_type, challenge_status, created_at, expires_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (username, channel) DO UPDATE SET
                   challenge_type = EXCLUDED.challenge_type,
                   challenge_status = 'pending',
                   created_at = EXCLUDED.created_at,
                   expires_at = EXCLUDED.expires_at,
                   completed_at = NULL""",
            (username, channel, challenge_type, "pending", now, expires_at),
        )
        await conn.commit()

    logger.info("Challenge created: user=%s type=%s channel=%s", username, challenge_type, channel)
    return {
        "username": username,
        "channel": channel,
        "challenge_type": challenge_type,
        "challenge_status": "pending",
        "created_at": now,
        "expires_at": expires_at,
    }


async def check_challenge(username: str, channel: str) -> Optional[dict]:
    """Check if a user has a pending challenge."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM user_challenges WHERE username = %s AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    if not result:
        return None

    challenge = dict(result)

    # Auto-complete wait challenges if expired
    if (
        challenge["challenge_status"] == "pending"
        and challenge["challenge_type"] == "wait"
        and challenge["expires_at"]
    ):
        try:
            expires = datetime.fromisoformat(challenge["expires_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= expires:
                await complete_challenge(username, channel)
                challenge["challenge_status"] = "completed"
                challenge["completed_at"] = _now_iso()
        except (ValueError, TypeError):
            pass

    return challenge


async def verify_challenge(
    username: str,
    channel: str,
    is_following: bool = False,
) -> dict:
    """Verify if a user has completed their challenge."""
    challenge = await check_challenge(username, channel)
    if not challenge:
        return {"status": "no_challenge", "completed": True}

    if challenge["challenge_status"] == "completed":
        return {"status": "already_completed", "completed": True}

    challenge_type = challenge["challenge_type"]

    if challenge_type == "follow" and is_following:
        await complete_challenge(username, channel)
        return {"status": "completed", "completed": True}

    if challenge_type == "wait":
        if challenge.get("expires_at"):
            try:
                expires = datetime.fromisoformat(challenge["expires_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) >= expires:
                    await complete_challenge(username, channel)
                    return {"status": "completed", "completed": True}
                remaining = (expires - datetime.now(timezone.utc)).total_seconds()
                return {
                    "status": "pending",
                    "completed": False,
                    "remaining_seconds": int(remaining),
                }
            except (ValueError, TypeError):
                pass

    return {"status": "pending", "completed": False}


async def complete_challenge(username: str, channel: str) -> None:
    """Mark a challenge as completed."""
    async with get_conn() as conn:
        await conn.execute(
            """UPDATE user_challenges SET challenge_status = 'completed', completed_at = %s
               WHERE username = %s AND channel = %s""",
            (_now_iso(), username, channel),
        )
        await conn.commit()
    logger.info("Challenge completed: user=%s channel=%s", username, channel)


async def list_active_challenges(channel: Optional[str] = None) -> list[dict]:
    """List all active (pending) challenges."""
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM user_challenges WHERE challenge_status = 'pending' AND channel = %s ORDER BY created_at DESC",
                (channel,),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM user_challenges WHERE challenge_status = 'pending' ORDER BY created_at DESC",
            )
        return [dict(r) for r in await row.fetchall()]
