"""Creator Economy Marketplace router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth, extract_user_id
from app.models.schemas import (
    MarketplaceItemCreate, MarketplaceItemUpdate,
    MarketplaceReviewCreate, SellerProfileCreate, SellerProfileUpdate,
)
from app.repositories import marketplace as mp_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


# ---------------------------------------------------------------------------
# Browse / Store
# ---------------------------------------------------------------------------

@router.get("/items")
async def list_items(
    category: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("newest"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """Browse published marketplace items."""
    return await mp_repo.list_items(
        category=category, search=search, sort=sort,
        limit=limit, offset=offset,
    )


@router.get("/items/{item_id}")
async def get_item(item_id: str) -> dict:
    """Get a single marketplace item."""
    item = await mp_repo.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/items/{item_id}/reviews")
async def get_item_reviews(item_id: str) -> list[dict]:
    """Get reviews for an item."""
    return await mp_repo.get_item_reviews(item_id)


# ---------------------------------------------------------------------------
# Seller Profile
# ---------------------------------------------------------------------------

@router.post("/seller/profile")
async def create_seller_profile(
    body: SellerProfileCreate, session: dict = Depends(require_auth),
) -> dict:
    """Create or update the current user's seller profile."""
    user_id = extract_user_id(session)
    return await mp_repo.create_seller_profile(
        user_id=user_id, display_name=body.display_name,
        bio=body.bio, avatar_url=body.avatar_url, website=body.website,
    )


@router.get("/seller/profile")
async def get_my_seller_profile(session: dict = Depends(require_auth)) -> dict:
    """Get the current user's seller profile."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found. Create one first.")
    return profile


@router.put("/seller/profile")
async def update_my_seller_profile(
    body: SellerProfileUpdate, session: dict = Depends(require_auth),
) -> dict:
    """Update the current user's seller profile."""
    user_id = extract_user_id(session)
    profile = await mp_repo.update_seller_profile(
        user_id=user_id, display_name=body.display_name,
        bio=body.bio, avatar_url=body.avatar_url, website=body.website,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return profile


@router.get("/sellers")
async def list_sellers(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """List active sellers."""
    return await mp_repo.list_sellers(limit=limit, offset=offset)


@router.get("/sellers/{profile_id}")
async def get_seller(profile_id: str) -> dict:
    """Get a seller profile by ID (public, sensitive fields redacted)."""
    profile = await mp_repo.get_seller_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Seller not found")
    # Redact sensitive financial data from public endpoint
    profile.pop("total_revenue", None)
    profile.pop("payout_info", None)
    return profile


# ---------------------------------------------------------------------------
# Seller Item Management
# ---------------------------------------------------------------------------

@router.post("/seller/items")
async def create_item(
    body: MarketplaceItemCreate, session: dict = Depends(require_auth),
) -> dict:
    """Create a new marketplace item for the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=400, detail="Create a seller profile first")
    return await mp_repo.create_item(
        seller_id=profile["id"], title=body.title, description=body.description,
        category=body.category, price=body.price, preview_url=body.preview_url,
        download_url=body.download_url, thumbnail_url=body.thumbnail_url,
        tags=body.tags,
    )


@router.get("/seller/items")
async def list_my_items(session: dict = Depends(require_auth)) -> list[dict]:
    """List all items for the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        return []
    return await mp_repo.get_seller_items(profile["id"])


@router.put("/seller/items/{item_id}")
async def update_item(
    item_id: str, body: MarketplaceItemUpdate,
    session: dict = Depends(require_auth),
) -> dict:
    """Update a marketplace item owned by the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=400, detail="Seller profile not found")
    item = await mp_repo.update_item(
        item_id=item_id, seller_id=profile["id"],
        title=body.title, description=body.description,
        category=body.category, price=body.price,
        preview_url=body.preview_url, download_url=body.download_url,
        thumbnail_url=body.thumbnail_url, tags=body.tags,
        status=body.status,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/seller/items/{item_id}")
async def delete_item(
    item_id: str, session: dict = Depends(require_auth),
) -> dict:
    """Delete a marketplace item owned by the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=400, detail="Seller profile not found")
    deleted = await mp_repo.delete_item(item_id, profile["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------

@router.post("/items/{item_id}/purchase")
async def purchase_item(
    item_id: str, session: dict = Depends(require_auth),
) -> dict:
    """Purchase a marketplace item."""
    user_id = extract_user_id(session)

    item = await mp_repo.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item["status"] != "published":
        raise HTTPException(status_code=400, detail="Item is not available for purchase")

    # Check if already purchased
    existing = await mp_repo.get_purchase(item_id, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="You already own this item")

    # Only allow free items to be purchased directly; paid items require
    # a payment flow (Stripe Connect / LemonSqueezy) that is not yet implemented.
    if item["price"] and item["price"] > 0:
        raise HTTPException(
            status_code=402,
            detail="Paid purchases require a payment flow. This feature is coming soon.",
        )

    purchase = await mp_repo.create_purchase(
        item_id=item_id,
        buyer_user_id=user_id,
        seller_id=item["seller_id"],
        price_paid=0,
    )
    return purchase


@router.get("/purchases")
async def get_my_purchases(session: dict = Depends(require_auth)) -> list[dict]:
    """Get the current user's purchases."""
    user_id = extract_user_id(session)
    return await mp_repo.get_user_purchases(user_id)


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@router.post("/items/{item_id}/reviews")
async def create_review(
    item_id: str, body: MarketplaceReviewCreate,
    session: dict = Depends(require_auth),
) -> dict:
    """Submit a review for an item (must have purchased it)."""
    user_id = extract_user_id(session)

    item = await mp_repo.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check purchase
    purchase = await mp_repo.get_purchase(item_id, user_id)
    if not purchase:
        raise HTTPException(status_code=403, detail="You must purchase the item before reviewing")

    return await mp_repo.create_review(
        item_id=item_id, user_id=user_id,
        rating=body.rating, comment=body.comment,
    )


# ---------------------------------------------------------------------------
# Seller Revenue & Payouts
# ---------------------------------------------------------------------------

@router.get("/seller/revenue")
async def get_my_revenue(session: dict = Depends(require_auth)) -> dict:
    """Get revenue analytics for the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return await mp_repo.get_seller_revenue_analytics(profile["id"])


@router.get("/seller/payouts")
async def get_my_payouts(session: dict = Depends(require_auth)) -> list[dict]:
    """Get payout history for the current seller."""
    user_id = extract_user_id(session)
    profile = await mp_repo.get_seller_profile_by_user(user_id)
    if not profile:
        return []
    return await mp_repo.get_seller_payouts(profile["id"])
