"""Kick API client with in-memory caching for stream and user data."""

import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

KICK_API_BASE = "https://kick.com/api"

# Simple in-memory cache with TTL
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 30


def _get_cached(key: str) -> Optional[dict]:
    """Return cached value if it exists and hasn't expired."""
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return data
        del _cache[key]
    return None


def _set_cached(key: str, data: dict) -> None:
    _cache[key] = (time.time(), data)


async def get_channel_info(channel: str) -> Optional[dict]:
    """Fetch channel/stream info from the Kick API.

    Returns a dict with keys: username, game, title, viewers, is_live, started_at
    or None if the request fails.
    """
    cache_key = f"channel:{channel}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{KICK_API_BASE}/v2/channels/{channel}",
                headers={"Accept": "application/json"},
            )
        if resp.status_code != 200:
            logger.warning("Kick API returned %s for channel %s", resp.status_code, channel)
            return None

        raw = resp.json()
        livestream = raw.get("livestream") or {}
        data = {
            "username": raw.get("slug", channel),
            "game": (livestream.get("categories") or [{}])[0].get("name", "Unknown") if livestream.get("categories") else (livestream.get("category", {}) or {}).get("name", "Unknown"),
            "title": livestream.get("session_title", ""),
            "viewers": livestream.get("viewer_count", 0),
            "is_live": livestream.get("is_live", False) if livestream else False,
            "started_at": livestream.get("created_at", ""),
            "follower_count": raw.get("followers_count", 0),
            "avatar_url": raw.get("profile_pic") or raw.get("user", {}).get("profile_pic", ""),
        }
        _set_cached(cache_key, data)
        return data
    except Exception:
        logger.exception("Failed to fetch Kick channel info for %s", channel)
        return None


async def get_user_profile(username: str) -> Optional[dict]:
    """Fetch a user's profile data from the Kick API.

    Returns a dict with keys: username, bio, avatar_url, follower_count,
    is_live, game, title, or None if the request fails.
    """
    cache_key = f"user:{username}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{KICK_API_BASE}/v2/channels/{username}",
                headers={"Accept": "application/json"},
            )
        if resp.status_code != 200:
            logger.warning("Kick API returned %s for user %s", resp.status_code, username)
            return None

        raw = resp.json()
        livestream = raw.get("livestream") or {}
        data = {
            "username": raw.get("slug", username),
            "bio": (raw.get("user", {}) or {}).get("bio", ""),
            "avatar_url": raw.get("profile_pic") or (raw.get("user", {}) or {}).get("profile_pic", ""),
            "follower_count": raw.get("followers_count", 0),
            "is_live": bool(livestream),
            "game": (livestream.get("categories") or [{}])[0].get("name", "") if livestream.get("categories") else (livestream.get("category", {}) or {}).get("name", ""),
            "title": livestream.get("session_title", "") if livestream else "",
            "verified": raw.get("verified", False),
        }
        _set_cached(cache_key, data)
        return data
    except Exception:
        logger.exception("Failed to fetch Kick user profile for %s", username)
        return None


def compute_uptime(started_at: str) -> str:
    """Compute human-readable uptime from a stream start timestamp."""
    if not started_at:
        return "offline"
    try:
        from datetime import datetime, timezone
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - start
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "unknown"


# List of supported command variables with descriptions
COMMAND_VARIABLES = [
    {"name": "{username}", "description": "The username of the person who triggered the command"},
    {"name": "{channel}", "description": "The channel name"},
    {"name": "{uptime}", "description": "Current stream uptime (e.g., 2h 15m)"},
    {"name": "{game}", "description": "The game/category currently being played"},
    {"name": "{title}", "description": "The current stream title"},
    {"name": "{viewers}", "description": "Current viewer count"},
    {"name": "{followers}", "description": "Total follower count"},
]


async def resolve_variables(text: str, channel: str, username: str = "viewer") -> str:
    """Replace all supported variables in a command response text."""
    if "{" not in text:
        return text

    result = text.replace("{username}", username)
    result = result.replace("{channel}", channel)

    # Only fetch API data if needed
    needs_api = any(var in result for var in ["{uptime}", "{game}", "{title}", "{viewers}", "{followers}"])
    if needs_api:
        info = await get_channel_info(channel)
        if info:
            result = result.replace("{uptime}", compute_uptime(info.get("started_at", "")))
            result = result.replace("{game}", info.get("game", "Unknown"))
            result = result.replace("{title}", info.get("title", ""))
            result = result.replace("{viewers}", str(info.get("viewers", 0)))
            result = result.replace("{followers}", str(info.get("follower_count", 0)))
        else:
            result = result.replace("{uptime}", "unavailable")
            result = result.replace("{game}", "unavailable")
            result = result.replace("{title}", "unavailable")
            result = result.replace("{viewers}", "0")
            result = result.replace("{followers}", "0")

    return result
