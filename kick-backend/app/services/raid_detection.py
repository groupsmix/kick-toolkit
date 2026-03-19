"""Raid detection service using sliding window analysis."""

import json
import logging
import time
from collections import defaultdict
from typing import Optional

from app.services.db import get_conn, _now_iso

logger = logging.getLogger(__name__)

# In-memory sliding window for real-time tracking
# Structure: { channel: [(username, timestamp), ...] }
_chat_windows: dict[str, list[tuple[str, float]]] = defaultdict(list)
_known_chatters: dict[str, set[str]] = defaultdict(set)


def record_chat_event(channel: str, username: str) -> None:
    """Record a chat event for raid detection (in-memory)."""
    now = time.time()
    _chat_windows[channel].append((username, now))
    _known_chatters[channel].add(username.lower())


def _clean_window(channel: str, window_seconds: int) -> None:
    """Remove expired entries from the sliding window."""
    cutoff = time.time() - window_seconds
    _chat_windows[channel] = [
        (u, t) for u, t in _chat_windows[channel] if t > cutoff
    ]


async def _get_settings() -> dict:
    """Get raid detection settings."""
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM raid_settings WHERE id = 1")
        result = await row.fetchone()
    if result:
        return dict(result)
    return {
        "enabled": True,
        "new_chatter_threshold": 20,
        "window_seconds": 60,
        "auto_action": "none",
        "min_account_age_days": 7,
    }


async def check_for_raid(channel: str) -> Optional[dict]:
    """Check if current chat activity indicates a raid.

    Returns raid event dict if detected, None otherwise.
    """
    settings = await _get_settings()
    if not settings.get("enabled", True):
        return None

    window_seconds = settings.get("window_seconds", 60)
    threshold = settings.get("new_chatter_threshold", 20)

    _clean_window(channel, window_seconds)

    # Count unique new chatters in the window
    window_users = set()
    for username, _ in _chat_windows[channel]:
        window_users.add(username.lower())

    new_chatter_count = len(window_users)

    if new_chatter_count < threshold:
        return None

    # Raid detected!
    severity = "low"
    if new_chatter_count >= threshold * 3:
        severity = "high"
    elif new_chatter_count >= threshold * 2:
        severity = "medium"

    suspicious = list(window_users)[:50]  # Cap at 50

    auto_action = settings.get("auto_action", "none")

    # Store raid event
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            """INSERT INTO raid_events
               (channel, detected_at, severity, new_chatters_count, window_seconds,
                suspicious_accounts, auto_action_taken)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (channel, now, severity, new_chatter_count, window_seconds,
             json.dumps(suspicious), auto_action),
        )
        result = await row.fetchone()
        await conn.commit()

    raid_id = result["id"] if result else None

    logger.warning(
        "Raid detected on channel=%s: %d new chatters in %ds (severity=%s)",
        channel, new_chatter_count, window_seconds, severity,
    )

    return {
        "id": raid_id,
        "channel": channel,
        "detected_at": now,
        "severity": severity,
        "new_chatters_count": new_chatter_count,
        "window_seconds": window_seconds,
        "suspicious_accounts": suspicious,
        "auto_action_taken": auto_action,
    }


async def list_raid_events(
    channel: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List detected raid events."""
    async with get_conn() as conn:
        if channel:
            row = await conn.execute(
                "SELECT * FROM raid_events WHERE channel = %s ORDER BY detected_at DESC LIMIT %s",
                (channel, limit),
            )
        else:
            row = await conn.execute(
                "SELECT * FROM raid_events ORDER BY detected_at DESC LIMIT %s",
                (limit,),
            )
        return [dict(r) for r in await row.fetchall()]


async def resolve_raid(raid_id: int) -> Optional[dict]:
    """Mark a raid event as resolved."""
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE raid_events SET resolved = TRUE, resolved_at = %s
               WHERE id = %s RETURNING *""",
            (_now_iso(), raid_id),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_raid_settings() -> dict:
    """Get raid detection settings."""
    return await _get_settings()


async def update_raid_settings(
    enabled: bool,
    new_chatter_threshold: int,
    window_seconds: int,
    auto_action: str,
    min_account_age_days: int,
) -> dict:
    """Update raid detection settings."""
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO raid_settings (id, enabled, new_chatter_threshold, window_seconds, auto_action, min_account_age_days)
               VALUES (1, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
                   enabled = EXCLUDED.enabled,
                   new_chatter_threshold = EXCLUDED.new_chatter_threshold,
                   window_seconds = EXCLUDED.window_seconds,
                   auto_action = EXCLUDED.auto_action,
                   min_account_age_days = EXCLUDED.min_account_age_days""",
            (enabled, new_chatter_threshold, window_seconds, auto_action, min_account_age_days),
        )
        await conn.commit()

    logger.info("Raid settings updated")
    return {
        "enabled": enabled,
        "new_chatter_threshold": new_chatter_threshold,
        "window_seconds": window_seconds,
        "auto_action": auto_action,
        "min_account_age_days": min_account_age_days,
    }
