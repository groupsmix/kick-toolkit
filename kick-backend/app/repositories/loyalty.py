"""Repository for loyalty points, rewards, and redemptions."""

from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


async def get_settings(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM loyalty_settings WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_settings(
    channel: str,
    enabled: bool,
    points_name: str,
    points_per_message: int,
    points_per_minute_watched: int,
    bonus_subscriber_multiplier: float,
    bonus_follower_multiplier: float,
    daily_bonus: int,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO loyalty_settings
               (channel, enabled, points_name, points_per_message, points_per_minute_watched,
                bonus_subscriber_multiplier, bonus_follower_multiplier, daily_bonus, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   enabled = EXCLUDED.enabled, points_name = EXCLUDED.points_name,
                   points_per_message = EXCLUDED.points_per_message,
                   points_per_minute_watched = EXCLUDED.points_per_minute_watched,
                   bonus_subscriber_multiplier = EXCLUDED.bonus_subscriber_multiplier,
                   bonus_follower_multiplier = EXCLUDED.bonus_follower_multiplier,
                   daily_bonus = EXCLUDED.daily_bonus, updated_at = EXCLUDED.updated_at""",
            (channel, enabled, points_name, points_per_message, points_per_minute_watched,
             bonus_subscriber_multiplier, bonus_follower_multiplier, daily_bonus, now),
        )
        await conn.commit()
    return {
        "channel": channel, "enabled": enabled, "points_name": points_name,
        "points_per_message": points_per_message,
        "points_per_minute_watched": points_per_minute_watched,
        "bonus_subscriber_multiplier": bonus_subscriber_multiplier,
        "bonus_follower_multiplier": bonus_follower_multiplier,
        "daily_bonus": daily_bonus, "updated_at": now,
    }


async def get_leaderboard(channel: str, limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT username, balance, total_earned, watch_time_minutes, message_count
               FROM loyalty_points WHERE channel = %s ORDER BY balance DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_user_points(channel: str, username: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM loyalty_points WHERE channel = %s AND username = %s",
            (channel, username),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def adjust_points(channel: str, username: str, amount: int) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM loyalty_points WHERE channel = %s AND username = %s",
            (channel, username),
        )
        existing = await row.fetchone()

        if existing:
            new_balance = max(0, existing["balance"] + amount)
            earned = existing["total_earned"] + amount if amount > 0 else existing["total_earned"]
            spent = existing["total_spent"] + abs(amount) if amount < 0 else existing["total_spent"]
            await conn.execute(
                """UPDATE loyalty_points SET balance = %s, total_earned = %s,
                   total_spent = %s, updated_at = %s
                   WHERE channel = %s AND username = %s""",
                (new_balance, earned, spent, now, channel, username),
            )
            result = {"username": username, "channel": channel, "balance": new_balance,
                       "total_earned": earned, "total_spent": spent}
        else:
            balance = max(0, amount)
            earned = amount if amount > 0 else 0
            await conn.execute(
                """INSERT INTO loyalty_points
                   (username, channel, balance, total_earned, total_spent,
                    watch_time_minutes, message_count, updated_at)
                   VALUES (%s, %s, %s, %s, 0, 0, 0, %s)""",
                (username, channel, balance, earned, now),
            )
            result = {"username": username, "channel": channel, "balance": balance,
                       "total_earned": earned, "total_spent": 0}
        await conn.commit()
    return result


async def list_rewards(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM loyalty_rewards WHERE channel = %s ORDER BY cost ASC",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def create_reward(
    channel: str, name: str, description: str, cost: int,
    reward_type: str, enabled: bool, max_redemptions: Optional[int],
) -> dict:
    reward_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO loyalty_rewards
               (id, channel, name, description, cost, type, enabled, max_redemptions, total_redemptions, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s)""",
            (reward_id, channel, name, description, cost, reward_type, enabled, max_redemptions, now),
        )
        await conn.commit()
    return {
        "id": reward_id, "channel": channel, "name": name, "description": description,
        "cost": cost, "type": reward_type, "enabled": enabled,
        "max_redemptions": max_redemptions, "total_redemptions": 0, "created_at": now,
    }


async def delete_reward(channel: str, reward_id: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM loyalty_rewards WHERE id = %s AND channel = %s",
            (reward_id, channel),
        )
        await conn.commit()


async def redeem_reward(channel: str, username: str, reward_id: str) -> Optional[dict]:
    async with get_conn() as conn:
        # Get the reward
        row = await conn.execute(
            "SELECT * FROM loyalty_rewards WHERE id = %s AND channel = %s",
            (reward_id, channel),
        )
        reward = await row.fetchone()
        if not reward or not reward["enabled"]:
            return None

        # Check max redemptions
        if reward["max_redemptions"] is not None and reward["total_redemptions"] >= reward["max_redemptions"]:
            return None

        # Check user balance
        row = await conn.execute(
            "SELECT balance FROM loyalty_points WHERE channel = %s AND username = %s",
            (channel, username),
        )
        user_pts = await row.fetchone()
        if not user_pts or user_pts["balance"] < reward["cost"]:
            return None

        # Deduct points
        new_balance = user_pts["balance"] - reward["cost"]
        now = _now_iso()
        await conn.execute(
            """UPDATE loyalty_points SET balance = %s, total_spent = total_spent + %s, updated_at = %s
               WHERE channel = %s AND username = %s""",
            (new_balance, reward["cost"], now, channel, username),
        )

        # Record redemption
        redemption_id = _generate_id()
        await conn.execute(
            """INSERT INTO loyalty_redemptions (id, channel, username, reward_id, reward_name, cost, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)""",
            (redemption_id, channel, username, reward_id, reward["name"], reward["cost"], now),
        )

        # Increment total redemptions
        await conn.execute(
            "UPDATE loyalty_rewards SET total_redemptions = total_redemptions + 1 WHERE id = %s",
            (reward_id,),
        )
        await conn.commit()

    return {
        "id": redemption_id, "channel": channel, "username": username,
        "reward_id": reward_id, "reward_name": reward["name"],
        "cost": reward["cost"], "status": "pending", "created_at": now,
    }


async def list_redemptions(channel: str, limit: int = 50) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM loyalty_redemptions WHERE channel = %s
               ORDER BY created_at DESC LIMIT %s""",
            (channel, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]
