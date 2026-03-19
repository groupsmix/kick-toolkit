"""LemonSqueezy payment integration service."""

import hashlib
import hmac
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LEMON_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
LEMON_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
LEMON_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")

# Map plan names to LemonSqueezy variant IDs
# These should be configured via environment variables
PLAN_VARIANT_IDS = {
    "pro": os.environ.get("LEMON_PRO_VARIANT_ID", ""),
    "premium": os.environ.get("LEMON_PREMIUM_VARIANT_ID", ""),
}

LEMON_API_BASE = "https://api.lemonsqueezy.com/v1"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LEMON_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


async def create_checkout(
    plan: str,
    user_id: str,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    success_url: Optional[str] = None,
) -> Optional[str]:
    """Create a LemonSqueezy checkout session and return the checkout URL."""
    variant_id = PLAN_VARIANT_IDS.get(plan)
    if not variant_id or not LEMON_STORE_ID:
        logger.warning("LemonSqueezy not configured: store_id=%s, variant_id=%s", LEMON_STORE_ID, variant_id)
        return None

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "custom": {
                        "user_id": user_id,
                        "plan": plan,
                    },
                },
                "product_options": {
                    "redirect_url": success_url or "",
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": LEMON_STORE_ID,
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": variant_id,
                    }
                },
            },
        }
    }

    if user_email:
        payload["data"]["attributes"]["checkout_data"]["email"] = user_email
    if user_name:
        payload["data"]["attributes"]["checkout_data"]["name"] = user_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LEMON_API_BASE}/checkouts",
            json=payload,
            headers=_headers(),
            timeout=15.0,
        )

        if response.status_code not in (200, 201):
            logger.error("LemonSqueezy checkout error: %s %s", response.status_code, response.text)
            return None

        data = response.json()
        checkout_url = data.get("data", {}).get("attributes", {}).get("url")
        return checkout_url


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the LemonSqueezy webhook signature."""
    if not LEMON_WEBHOOK_SECRET:
        logger.warning("LEMONSQUEEZY_WEBHOOK_SECRET not set, skipping verification")
        return True  # Allow in dev mode

    computed = hmac.new(
        LEMON_WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


def parse_webhook_event(payload: dict) -> dict:
    """Parse a LemonSqueezy webhook event into a simplified dict."""
    meta = payload.get("meta", {})
    event_name = meta.get("event_name", "")
    custom_data = meta.get("custom_data", {})

    attributes = payload.get("data", {}).get("attributes", {})

    return {
        "event": event_name,
        "user_id": custom_data.get("user_id", ""),
        "plan": custom_data.get("plan", ""),
        "subscription_id": str(payload.get("data", {}).get("id", "")),
        "customer_id": str(attributes.get("customer_id", "")),
        "order_id": str(attributes.get("order_id", "")),
        "status": attributes.get("status", ""),
        "renews_at": attributes.get("renews_at"),
        "ends_at": attributes.get("ends_at"),
        "current_period_end": attributes.get("renews_at"),
    }
