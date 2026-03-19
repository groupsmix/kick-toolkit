"""Repository for anti-alt detection data access."""

import json
from typing import Optional

from app.services.db import get_conn, _now_iso


async def get_flagged_account(username: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM flagged_accounts WHERE lower(username) = lower(%s)", (username,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def insert_flagged_account(
    username: str, risk_score: float, risk_level: str, flags: list[str],
    account_age_days: int, follower_count: int, is_following: bool,
) -> None:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO flagged_accounts (username, risk_score, risk_level, flags, account_age_days,
               follower_count, is_following, similar_names, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (username) DO UPDATE SET risk_score = EXCLUDED.risk_score""",
            (username, risk_score, risk_level, json.dumps(flags), account_age_days,
             follower_count, is_following, "[]", now),
        )
        await conn.commit()


async def list_flagged() -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM flagged_accounts ORDER BY risk_score DESC")
        return [dict(a) for a in await row.fetchall()]


async def get_settings() -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM anti_alt_settings WHERE id = 1")
        result = await row.fetchone()
    return dict(result) if result else None


async def get_timeout_threshold() -> float:
    async with get_conn() as conn:
        row = await conn.execute("SELECT auto_timeout_threshold FROM anti_alt_settings WHERE id = 1")
        settings = await row.fetchone()
    return settings["auto_timeout_threshold"] if settings else 50.0


async def upsert_settings(settings: object) -> None:
    """Upsert anti-alt settings from an AntiAltSettings model."""
    data = settings.model_dump() if hasattr(settings, "model_dump") else dict(settings)  # type: ignore[union-attr]
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO anti_alt_settings (
                   id, enabled, min_account_age_days, auto_ban_threshold,
                   auto_timeout_threshold, check_name_similarity, check_follow_status,
                   whitelisted_users, challenge_enabled, challenge_type,
                   challenge_wait_minutes, challenge_message,
                   auto_whitelist_enabled, auto_whitelist_min_messages,
                   auto_whitelist_min_follow_days
               ) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
                   enabled = EXCLUDED.enabled,
                   min_account_age_days = EXCLUDED.min_account_age_days,
                   auto_ban_threshold = EXCLUDED.auto_ban_threshold,
                   auto_timeout_threshold = EXCLUDED.auto_timeout_threshold,
                   check_name_similarity = EXCLUDED.check_name_similarity,
                   check_follow_status = EXCLUDED.check_follow_status,
                   whitelisted_users = EXCLUDED.whitelisted_users,
                   challenge_enabled = EXCLUDED.challenge_enabled,
                   challenge_type = EXCLUDED.challenge_type,
                   challenge_wait_minutes = EXCLUDED.challenge_wait_minutes,
                   challenge_message = EXCLUDED.challenge_message,
                   auto_whitelist_enabled = EXCLUDED.auto_whitelist_enabled,
                   auto_whitelist_min_messages = EXCLUDED.auto_whitelist_min_messages,
                   auto_whitelist_min_follow_days = EXCLUDED.auto_whitelist_min_follow_days""",
            (
                data.get("enabled", True),
                data.get("min_account_age_days", 7),
                data.get("auto_ban_threshold", 80.0),
                data.get("auto_timeout_threshold", 50.0),
                data.get("check_name_similarity", True),
                data.get("check_follow_status", True),
                json.dumps(data.get("whitelisted_users", [])),
                data.get("challenge_enabled", False),
                data.get("challenge_type", "follow"),
                data.get("challenge_wait_minutes", 10),
                data.get("challenge_message", ""),
                data.get("auto_whitelist_enabled", True),
                data.get("auto_whitelist_min_messages", 100),
                data.get("auto_whitelist_min_follow_days", 30),
            ),
        )
        await conn.commit()


async def remove_flagged(username: str) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM flagged_accounts WHERE lower(username) = lower(%s)", (username,))
        await conn.commit()


async def whitelist_user(username: str) -> None:
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
