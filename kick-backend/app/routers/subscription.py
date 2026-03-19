"""Subscription management API routes."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import require_auth
from app.repositories import subscription as sub_repo
from app.services import lemonsqueezy as lemon

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["subscription"])
webhook_router = APIRouter(tags=["webhooks"])


@router.get("/plans")
async def get_plans():
    """Return all available subscription plans."""
    return {"plans": sub_repo.get_plans()}


@router.get("/me")
async def get_my_subscription(session: dict = Depends(require_auth)):
    """Get the current user's subscription and usage."""
    user_data = session.get("user_data")
    if isinstance(user_data, str):
        user_data = json.loads(user_data)

    user_id = str(user_data.get("user_id", "")) if user_data else ""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in session")

    # Get or create subscription
    sub = await sub_repo.get_subscription(user_id)
    if not sub:
        sub = await sub_repo.create_or_update_subscription(user_id, plan="free")

    plan_info = sub_repo.get_plan(sub["plan"]) or sub_repo.get_plan("free")
    usage = await sub_repo.get_usage(user_id)

    return {
        "subscription": sub,
        "plan": plan_info,
        "usage": usage,
    }


@router.post("/checkout")
async def create_checkout(
    plan: str,
    session: dict = Depends(require_auth),
):
    """Create a LemonSqueezy checkout session for a plan upgrade."""
    if plan not in ("pro", "premium"):
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'pro' or 'premium'")

    user_data = session.get("user_data")
    if isinstance(user_data, str):
        user_data = json.loads(user_data)

    user_id = str(user_data.get("user_id", "")) if user_data else ""
    user_email = user_data.get("email") if user_data else None
    user_name = user_data.get("name") if user_data else None

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in session")

    checkout_url = await lemon.create_checkout(
        plan=plan,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
    )

    if not checkout_url:
        raise HTTPException(
            status_code=503,
            detail="Payment service not configured. Please contact support.",
        )

    return {"checkout_url": checkout_url}


@webhook_router.post("/api/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    """Handle LemonSqueezy webhook events for subscription management."""
    body = await request.body()
    signature = request.headers.get("x-signature", "")

    if not lemon.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = lemon.parse_webhook_event(payload)
    event_name = event["event"]
    user_id = event["user_id"]

    logger.info("LemonSqueezy webhook: event=%s user_id=%s", event_name, user_id)

    if not user_id:
        logger.warning("Webhook missing user_id in custom_data")
        return {"status": "ignored", "reason": "no user_id"}

    if event_name == "subscription_created":
        await sub_repo.create_or_update_subscription(
            user_id=user_id,
            plan=event["plan"],
            status="active",
            lemon_subscription_id=event["subscription_id"],
            lemon_customer_id=event["customer_id"],
            lemon_order_id=event["order_id"],
            current_period_end=event["current_period_end"],
        )
    elif event_name == "subscription_updated":
        status = event["status"]
        plan = event["plan"]
        # Map LemonSqueezy status to our status
        status_map = {
            "active": "active",
            "paused": "cancelled",
            "past_due": "past_due",
            "unpaid": "past_due",
            "cancelled": "cancelled",
            "expired": "expired",
        }
        mapped_status = status_map.get(status, "active")

        await sub_repo.create_or_update_subscription(
            user_id=user_id,
            plan=plan or "free",
            status=mapped_status,
            lemon_subscription_id=event["subscription_id"],
            current_period_end=event["current_period_end"],
        )
    elif event_name in ("subscription_cancelled", "subscription_expired"):
        await sub_repo.create_or_update_subscription(
            user_id=user_id,
            plan="free",
            status="cancelled" if "cancelled" in event_name else "expired",
        )

    return {"status": "ok"}
