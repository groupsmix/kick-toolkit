"""Repository for dashboard stats data access."""

import logging

from app.services.db import get_conn
from app.services.redis_cache import get_cached, set_cached

logger = logging.getLogger(__name__)

_CACHE_TTL = 15  # seconds


async def get_stats(channel: str) -> dict:
    """Return dashboard statistics scoped to *channel*.

    All counts are filtered by the channel column so that users only see
    their own data.  The 10 original sequential COUNT queries have been
    collapsed into a single round-trip using sub-selects, and the result
    is cached for 15 seconds to avoid hammering the database on every
    dashboard poll.
    """
    cache_key = f"dashboard:stats:{channel}"
    cached = await get_cached(cache_key, ttl=_CACHE_TTL)
    if cached is not None:
        return cached

    async with get_conn() as conn:
        row = await conn.execute(
            """
            SELECT
                (SELECT count(*)                  FROM chat_logs          WHERE channel = %(ch)s)                               AS total_messages,
                (SELECT count(*)                  FROM chat_logs          WHERE channel = %(ch)s AND flagged = TRUE)             AS flagged_messages,
                (SELECT count(DISTINCT username)  FROM chat_logs          WHERE channel = %(ch)s)                               AS unique_users,
                (SELECT count(*)                  FROM giveaways          WHERE channel = %(ch)s AND status = 'active')         AS active_giveaways,
                (SELECT count(*)                  FROM tournaments        WHERE channel = %(ch)s AND status IN ('registration', 'in_progress')) AS active_tournaments,
                (SELECT count(*)                  FROM flagged_accounts   WHERE channel = %(ch)s)                               AS flagged_accounts,
                (SELECT count(*)                  FROM bot_commands       WHERE channel = %(ch)s)                               AS total_commands,
                (SELECT count(*)                  FROM banned_users       WHERE channel = %(ch)s)                               AS banned_users,
                (SELECT count(*)                  FROM whitelisted_users  WHERE channel = %(ch)s)                               AS whitelisted_users,
                (SELECT count(*)                  FROM raid_events        WHERE channel = %(ch)s AND resolved = FALSE)          AS active_raids,
                (SELECT count(*)                  FROM user_challenges    WHERE channel = %(ch)s AND challenge_status = 'pending') AS pending_challenges
            """,
            {"ch": channel},
        )
        result = await row.fetchone()

    total_messages = result["total_messages"]
    flagged_messages = result["flagged_messages"]
    moderation_rate = round(flagged_messages / max(total_messages, 1) * 100, 1)

    stats = {
        "total_messages": total_messages,
        "flagged_messages": flagged_messages,
        "unique_users": result["unique_users"],
        "active_giveaways": result["active_giveaways"],
        "active_tournaments": result["active_tournaments"],
        "flagged_accounts": result["flagged_accounts"],
        "total_commands": result["total_commands"],
        "moderation_rate": moderation_rate,
        "banned_users": result["banned_users"],
        "whitelisted_users": result["whitelisted_users"],
        "active_raids": result["active_raids"],
        "pending_challenges": result["pending_challenges"],
    }

    await set_cached(cache_key, stats, ttl=_CACHE_TTL)
    return stats
