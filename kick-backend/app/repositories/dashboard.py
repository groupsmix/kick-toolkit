"""Repository for dashboard stats data access."""

from app.services.db import get_conn


async def get_stats() -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs")
        total_messages = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs WHERE flagged = TRUE")
        flagged_messages = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(DISTINCT username) AS cnt FROM chat_logs")
        unique_users = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM giveaways WHERE status = 'active'")
        active_giveaways = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM tournaments WHERE status IN ('registration', 'in_progress')")
        active_tournaments = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM flagged_accounts")
        flagged_accounts_count = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM bot_commands")
        total_commands = (await row.fetchone())["cnt"]

    moderation_rate = round(flagged_messages / max(total_messages, 1) * 100, 1)

    return {
        "total_messages": total_messages,
        "flagged_messages": flagged_messages,
        "unique_users": unique_users,
        "active_giveaways": active_giveaways,
        "active_tournaments": active_tournaments,
        "flagged_accounts": flagged_accounts_count,
        "total_commands": total_commands,
        "moderation_rate": moderation_rate,
    }
