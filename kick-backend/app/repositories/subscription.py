"""Subscription repository — database operations for subscriptions."""

import json
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


# Plan definitions with feature limits
PLANS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price": 0.0,
        "currency": "USD",
        "interval": "month",
        "features": [
            "Dashboard overview",
            "5 bot commands",
            "100 chat log entries",
            "1 active giveaway",
            "Community support",
        ],
        "limits": {
            "bot_commands": 5,
            "chat_log_entries": 100,
            "active_giveaways": 1,
            "ai_moderation": 0,
            "anti_alt": 0,
            "tournaments": 0,
            "custom_alerts": 0,
            "analytics": 0,
            "api_access": 0,
        },
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price": 9.99,
        "currency": "USD",
        "interval": "month",
        "features": [
            "Everything in Free",
            "Unlimited bot commands",
            "Unlimited chat logs",
            "AI moderation",
            "Unlimited giveaways",
            "Chat analytics",
            "Priority support",
        ],
        "limits": {
            "bot_commands": -1,  # -1 = unlimited
            "chat_log_entries": -1,
            "active_giveaways": -1,
            "ai_moderation": 1,
            "anti_alt": 0,
            "tournaments": 0,
            "custom_alerts": 0,
            "analytics": 1,
            "api_access": 0,
        },
    },
    "premium": {
        "id": "premium",
        "name": "Premium",
        "price": 24.99,
        "currency": "USD",
        "interval": "month",
        "features": [
            "Everything in Pro",
            "Anti-alt detection",
            "Tournament organizer",
            "Custom alerts & overlays",
            "Advanced analytics",
            "API access",
            "Dedicated support",
        ],
        "limits": {
            "bot_commands": -1,
            "chat_log_entries": -1,
            "active_giveaways": -1,
            "ai_moderation": 1,
            "anti_alt": 1,
            "tournaments": 1,
            "custom_alerts": 1,
            "analytics": 1,
            "api_access": 1,
        },
    },
}


def get_plans() -> list[dict]:
    """Return all available plans."""
    return list(PLANS.values())


def get_plan(plan_id: str) -> Optional[dict]:
    """Return a specific plan by ID."""
    return PLANS.get(plan_id)


async def get_subscription(user_id: str) -> Optional[dict]:
    """Get the subscription for a user."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = %s",
            (user_id,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def create_or_update_subscription(
    user_id: str,
    plan: str = "free",
    status: str = "active",
    lemon_subscription_id: Optional[str] = None,
    lemon_customer_id: Optional[str] = None,
    lemon_order_id: Optional[str] = None,
    current_period_start: Optional[str] = None,
    current_period_end: Optional[str] = None,
) -> dict:
    """Create or update a subscription for a user."""
    now = _now_iso()
    sub_id = _generate_id()

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO subscriptions (id, user_id, plan, status, lemon_subscription_id,
               lemon_customer_id, lemon_order_id, current_period_start, current_period_end,
               created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (user_id) DO UPDATE SET
                   plan = EXCLUDED.plan,
                   status = EXCLUDED.status,
                   lemon_subscription_id = COALESCE(EXCLUDED.lemon_subscription_id, subscriptions.lemon_subscription_id),
                   lemon_customer_id = COALESCE(EXCLUDED.lemon_customer_id, subscriptions.lemon_customer_id),
                   lemon_order_id = COALESCE(EXCLUDED.lemon_order_id, subscriptions.lemon_order_id),
                   current_period_start = COALESCE(EXCLUDED.current_period_start, subscriptions.current_period_start),
                   current_period_end = COALESCE(EXCLUDED.current_period_end, subscriptions.current_period_end),
                   updated_at = EXCLUDED.updated_at""",
            (sub_id, user_id, plan, status, lemon_subscription_id,
             lemon_customer_id, lemon_order_id, current_period_start,
             current_period_end, now, now),
        )
        await conn.commit()

    sub = await get_subscription(user_id)
    return sub if sub else {"id": sub_id, "user_id": user_id, "plan": plan, "status": status}


async def get_usage(user_id: str) -> dict:
    """Get usage counts for a user."""
    async with get_conn() as conn:
        # Count bot commands
        row = await conn.execute(
            "SELECT count(*) AS cnt FROM bot_commands",
        )
        result = await row.fetchone()
        bot_commands = result["cnt"] if result else 0

        # Count chat logs
        row = await conn.execute(
            "SELECT count(*) AS cnt FROM chat_logs",
        )
        result = await row.fetchone()
        chat_logs = result["cnt"] if result else 0

        # Count active giveaways
        row = await conn.execute(
            "SELECT count(*) AS cnt FROM giveaways WHERE status = 'active'",
        )
        result = await row.fetchone()
        active_giveaways = result["cnt"] if result else 0

    return {
        "bot_commands": bot_commands,
        "chat_log_entries": chat_logs,
        "active_giveaways": active_giveaways,
    }
