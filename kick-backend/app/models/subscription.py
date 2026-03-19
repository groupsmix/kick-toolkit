"""Subscription and payment schemas."""

from pydantic import BaseModel
from typing import Optional


class SubscriptionPlan(BaseModel):
    id: str  # "free", "pro", "premium"
    name: str
    price: float
    currency: str = "USD"
    interval: str = "month"
    features: list[str] = []
    limits: dict[str, int] = {}


class Subscription(BaseModel):
    id: str
    user_id: str
    plan: str = "free"  # "free", "pro", "premium"
    status: str = "active"  # "active", "cancelled", "past_due", "expired"
    lemon_subscription_id: Optional[str] = None
    lemon_customer_id: Optional[str] = None
    lemon_order_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "premium"


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionUsage(BaseModel):
    plan: str
    plan_name: str
    status: str
    limits: dict[str, int]
    usage: dict[str, int]
