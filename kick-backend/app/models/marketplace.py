"""Creator economy marketplace schemas."""

from pydantic import BaseModel
from typing import Optional


class SellerProfileCreate(BaseModel):
    display_name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class SellerProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None


class SellerProfile(BaseModel):
    id: Optional[str] = None
    user_id: str
    display_name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    total_sales: int = 0
    total_revenue: float = 0.0
    rating_avg: float = 0.0
    rating_count: int = 0
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MarketplaceItemCreate(BaseModel):
    title: str
    description: str = ""
    category: str = "overlay"  # "overlay", "alert_pack", "widget_skin", "chatbot_preset"
    price: float = 0.0
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: list[str] = []


class MarketplaceItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None


class MarketplaceItem(BaseModel):
    id: Optional[str] = None
    seller_id: str
    title: str
    description: str = ""
    category: str = "overlay"
    price: float = 0.0
    currency: str = "USD"
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: list[str] = []
    status: str = "draft"
    download_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MarketplacePurchase(BaseModel):
    id: Optional[str] = None
    item_id: str
    buyer_user_id: str
    seller_id: str
    price_paid: float = 0.0
    platform_fee: float = 0.0
    seller_payout: float = 0.0
    status: str = "completed"
    payment_reference: Optional[str] = None
    created_at: Optional[str] = None


class MarketplaceReviewCreate(BaseModel):
    rating: int = 5  # 1-5
    comment: str = ""


class MarketplaceReview(BaseModel):
    id: Optional[str] = None
    item_id: str
    user_id: str
    rating: int = 5
    comment: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SellerPayout(BaseModel):
    id: Optional[str] = None
    seller_id: str
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    payment_method: str = "stripe"
    payment_reference: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    created_at: Optional[str] = None
    paid_at: Optional[str] = None


class SellerRevenueAnalytics(BaseModel):
    seller_id: str
    total_revenue: float = 0.0
    total_sales: int = 0
    platform_fees: float = 0.0
    net_revenue: float = 0.0
    pending_payout: float = 0.0
    items_listed: int = 0
    avg_item_rating: float = 0.0
    monthly_revenue: list[dict] = []
    top_items: list[dict] = []
