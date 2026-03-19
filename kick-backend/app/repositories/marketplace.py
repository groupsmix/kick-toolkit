"""Repository for Creator Economy Marketplace data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso

PLATFORM_FEE_RATE = 0.20  # 20% revenue share


# ---------------------------------------------------------------------------
# Seller Profiles
# ---------------------------------------------------------------------------

async def create_seller_profile(
    user_id: str, display_name: str, bio: str = "",
    avatar_url: str | None = None, website: str | None = None,
) -> dict:
    profile_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO seller_profiles
               (id, user_id, display_name, bio, avatar_url, website, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (user_id) DO UPDATE SET
                 display_name = EXCLUDED.display_name,
                 bio = EXCLUDED.bio,
                 avatar_url = COALESCE(EXCLUDED.avatar_url, seller_profiles.avatar_url),
                 website = COALESCE(EXCLUDED.website, seller_profiles.website),
                 updated_at = EXCLUDED.updated_at""",
            (profile_id, user_id, display_name, bio, avatar_url, website, now, now),
        )
        await conn.commit()
    return await get_seller_profile_by_user(user_id) or {
        "id": profile_id, "user_id": user_id, "display_name": display_name,
        "bio": bio, "avatar_url": avatar_url, "website": website,
        "total_sales": 0, "total_revenue": 0.0, "rating_avg": 0.0,
        "rating_count": 0, "status": "active", "created_at": now, "updated_at": now,
    }


async def get_seller_profile(profile_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM seller_profiles WHERE id = %s", (profile_id,)
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_seller_profile_by_user(user_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM seller_profiles WHERE user_id = %s", (user_id,)
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def update_seller_profile(user_id: str, **kwargs: object) -> dict | None:
    now = _now_iso()
    allowed = {"display_name", "bio", "avatar_url", "website"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return await get_seller_profile_by_user(user_id)

    set_parts = [f"{k} = %s" for k in updates]
    set_parts.append("updated_at = %s")
    values = list(updates.values())
    values.append(now)
    values.append(user_id)

    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE seller_profiles SET {', '.join(set_parts)} WHERE user_id = %s",
            tuple(values),
        )
        await conn.commit()
    return await get_seller_profile_by_user(user_id)


async def list_sellers(limit: int = 50, offset: int = 0) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM seller_profiles WHERE status = 'active'
               ORDER BY total_sales DESC LIMIT %s OFFSET %s""",
            (limit, offset),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Marketplace Items
# ---------------------------------------------------------------------------

async def create_item(
    seller_id: str, title: str, description: str = "", category: str = "overlay",
    price: float = 0.0, preview_url: str | None = None, download_url: str | None = None,
    thumbnail_url: str | None = None, tags: list[str] | None = None,
) -> dict:
    item_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO marketplace_items
               (id, seller_id, title, description, category, price, preview_url,
                download_url, thumbnail_url, tags, status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published',%s,%s)""",
            (item_id, seller_id, title, description, category, price,
             preview_url, download_url, thumbnail_url,
             json.dumps(tags or []), now, now),
        )
        await conn.commit()
    return {
        "id": item_id, "seller_id": seller_id, "title": title,
        "description": description, "category": category, "price": price,
        "currency": "USD", "preview_url": preview_url, "download_url": download_url,
        "thumbnail_url": thumbnail_url, "tags": tags or [],
        "status": "published", "download_count": 0,
        "rating_avg": 0.0, "rating_count": 0,
        "created_at": now, "updated_at": now,
    }


async def get_item(item_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM marketplace_items WHERE id = %s", (item_id,)
        )
        row = await cur.fetchone()
    if not row:
        return None
    d = dict(row)
    if isinstance(d.get("tags"), str):
        d["tags"] = json.loads(d["tags"])
    return d


async def update_item(item_id: str, seller_id: str, **kwargs: object) -> dict | None:
    now = _now_iso()
    allowed = {"title", "description", "category", "price", "preview_url",
               "download_url", "thumbnail_url", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}

    tags = kwargs.get("tags")
    if tags is not None:
        updates["tags"] = json.dumps(tags)

    if not updates:
        return await get_item(item_id)

    set_parts = [f"{k} = %s" for k in updates]
    set_parts.append("updated_at = %s")
    values = list(updates.values())
    values.append(now)
    values.append(item_id)
    values.append(seller_id)

    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE marketplace_items SET {', '.join(set_parts)} WHERE id = %s AND seller_id = %s",
            tuple(values),
        )
        await conn.commit()
    return await get_item(item_id)


async def delete_item(item_id: str, seller_id: str) -> bool:
    async with get_conn() as conn:
        result = await conn.execute(
            "DELETE FROM marketplace_items WHERE id = %s AND seller_id = %s",
            (item_id, seller_id),
        )
        await conn.commit()
        return result.rowcount > 0


async def list_items(
    category: str | None = None, search: str | None = None,
    seller_id: str | None = None, status: str = "published",
    sort: str = "newest", limit: int = 50, offset: int = 0,
) -> list[dict]:
    conditions = []
    params: list[object] = []

    if status:
        conditions.append("status = %s")
        params.append(status)
    if category:
        conditions.append("category = %s")
        params.append(category)
    if seller_id:
        conditions.append("seller_id = %s")
        params.append(seller_id)
    if search:
        conditions.append("(title ILIKE %s OR description ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    order = "ORDER BY created_at DESC"
    if sort == "popular":
        order = "ORDER BY download_count DESC"
    elif sort == "price_low":
        order = "ORDER BY price ASC"
    elif sort == "price_high":
        order = "ORDER BY price DESC"
    elif sort == "rating":
        order = "ORDER BY rating_avg DESC"

    params.extend([limit, offset])

    async with get_conn() as conn:
        cur = await conn.execute(
            f"SELECT * FROM marketplace_items {where} {order} LIMIT %s OFFSET %s",
            tuple(params),
        )
        rows = await cur.fetchall()

    items = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("tags"), str):
            d["tags"] = json.loads(d["tags"])
        items.append(d)
    return items


async def get_seller_items(seller_id: str) -> list[dict]:
    """Get all items for a seller (any status)."""
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM marketplace_items WHERE seller_id = %s ORDER BY created_at DESC",
            (seller_id,),
        )
        rows = await cur.fetchall()

    items = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("tags"), str):
            d["tags"] = json.loads(d["tags"])
        items.append(d)
    return items


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------

async def create_purchase(
    item_id: str, buyer_user_id: str, seller_id: str, price_paid: float,
    payment_reference: str | None = None,
) -> dict:
    purchase_id = _generate_id()
    now = _now_iso()
    platform_fee = round(price_paid * PLATFORM_FEE_RATE, 2)
    seller_payout = round(price_paid - platform_fee, 2)

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO marketplace_purchases
               (id, item_id, buyer_user_id, seller_id, price_paid, platform_fee,
                seller_payout, status, payment_reference, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'completed',%s,%s)""",
            (purchase_id, item_id, buyer_user_id, seller_id, price_paid,
             platform_fee, seller_payout, payment_reference, now),
        )
        # Update item download count
        await conn.execute(
            "UPDATE marketplace_items SET download_count = download_count + 1 WHERE id = %s",
            (item_id,),
        )
        # Update seller stats
        await conn.execute(
            """UPDATE seller_profiles SET
                 total_sales = total_sales + 1,
                 total_revenue = total_revenue + %s,
                 updated_at = %s
               WHERE id = %s""",
            (seller_payout, now, seller_id),
        )
        await conn.commit()

    return {
        "id": purchase_id, "item_id": item_id, "buyer_user_id": buyer_user_id,
        "seller_id": seller_id, "price_paid": price_paid,
        "platform_fee": platform_fee, "seller_payout": seller_payout,
        "status": "completed", "payment_reference": payment_reference,
        "created_at": now,
    }


async def get_purchase(item_id: str, buyer_user_id: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM marketplace_purchases WHERE item_id = %s AND buyer_user_id = %s",
            (item_id, buyer_user_id),
        )
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_user_purchases(user_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT p.*, i.title, i.category, i.thumbnail_url, i.download_url
               FROM marketplace_purchases p
               JOIN marketplace_items i ON p.item_id = i.id
               WHERE p.buyer_user_id = %s
               ORDER BY p.created_at DESC""",
            (user_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

async def create_review(
    item_id: str, user_id: str, rating: int, comment: str = "",
) -> dict:
    review_id = _generate_id()
    now = _now_iso()
    rating = max(1, min(5, rating))

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO marketplace_reviews
               (id, item_id, user_id, rating, comment, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (item_id, user_id) DO UPDATE SET
                 rating = EXCLUDED.rating,
                 comment = EXCLUDED.comment,
                 updated_at = EXCLUDED.updated_at""",
            (review_id, item_id, user_id, rating, comment, now, now),
        )
        # Update item rating average
        cur = await conn.execute(
            "SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt FROM marketplace_reviews WHERE item_id = %s",
            (item_id,),
        )
        row = await cur.fetchone()
        avg_rating = row["avg_r"] if row and row["avg_r"] else 0.0
        count = row["cnt"] if row else 0
        await conn.execute(
            "UPDATE marketplace_items SET rating_avg = %s, rating_count = %s WHERE id = %s",
            (round(float(avg_rating), 2), count, item_id),
        )
        # Also update seller average rating
        item = await (await conn.execute(
            "SELECT seller_id FROM marketplace_items WHERE id = %s", (item_id,)
        )).fetchone()
        if item:
            cur2 = await conn.execute(
                """SELECT AVG(r.rating) AS avg_r, COUNT(*) AS cnt
                   FROM marketplace_reviews r
                   JOIN marketplace_items i ON r.item_id = i.id
                   WHERE i.seller_id = %s""",
                (item["seller_id"],),
            )
            srow = await cur2.fetchone()
            s_avg = srow["avg_r"] if srow and srow["avg_r"] else 0.0
            s_cnt = srow["cnt"] if srow else 0
            await conn.execute(
                "UPDATE seller_profiles SET rating_avg = %s, rating_count = %s WHERE id = %s",
                (round(float(s_avg), 2), s_cnt, item["seller_id"]),
            )
        await conn.commit()

    return {
        "id": review_id, "item_id": item_id, "user_id": user_id,
        "rating": rating, "comment": comment,
        "created_at": now, "updated_at": now,
    }


async def get_item_reviews(item_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM marketplace_reviews WHERE item_id = %s ORDER BY created_at DESC",
            (item_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Payouts
# ---------------------------------------------------------------------------

async def get_seller_payouts(seller_id: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM seller_payouts WHERE seller_id = %s ORDER BY created_at DESC",
            (seller_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def create_payout(
    seller_id: str, amount: float, period_start: str, period_end: str,
    payment_method: str = "stripe",
) -> dict:
    payout_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO seller_payouts
               (id, seller_id, amount, currency, status, payment_method,
                period_start, period_end, created_at)
               VALUES (%s,%s,%s,'USD','pending',%s,%s,%s,%s)""",
            (payout_id, seller_id, amount, payment_method, period_start, period_end, now),
        )
        await conn.commit()
    return {
        "id": payout_id, "seller_id": seller_id, "amount": amount,
        "currency": "USD", "status": "pending", "payment_method": payment_method,
        "payment_reference": None, "period_start": period_start,
        "period_end": period_end, "created_at": now, "paid_at": None,
    }


# ---------------------------------------------------------------------------
# Revenue Analytics
# ---------------------------------------------------------------------------

async def get_seller_revenue_analytics(seller_id: str) -> dict:
    async with get_conn() as conn:
        # Total revenue and sales
        cur = await conn.execute(
            """SELECT COUNT(*) AS total_sales,
                      COALESCE(SUM(seller_payout), 0) AS net_revenue,
                      COALESCE(SUM(platform_fee), 0) AS platform_fees,
                      COALESCE(SUM(price_paid), 0) AS total_revenue
               FROM marketplace_purchases WHERE seller_id = %s AND status = 'completed'""",
            (seller_id,),
        )
        stats = await cur.fetchone()

        # Pending payout
        cur = await conn.execute(
            """SELECT COALESCE(SUM(amount), 0) AS pending
               FROM seller_payouts WHERE seller_id = %s AND status = 'pending'""",
            (seller_id,),
        )
        payout_row = await cur.fetchone()

        # Items listed
        cur = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM marketplace_items WHERE seller_id = %s",
            (seller_id,),
        )
        items_row = await cur.fetchone()

        # Seller rating
        profile = await (await conn.execute(
            "SELECT rating_avg FROM seller_profiles WHERE id = %s", (seller_id,)
        )).fetchone()

        # Top items by sales
        cur = await conn.execute(
            """SELECT i.id, i.title, i.category, i.price, i.download_count, i.rating_avg
               FROM marketplace_items i WHERE i.seller_id = %s
               ORDER BY i.download_count DESC LIMIT 5""",
            (seller_id,),
        )
        top_items = [dict(r) for r in await cur.fetchall()]

    return {
        "seller_id": seller_id,
        "total_revenue": float(stats["total_revenue"]) if stats else 0.0,
        "total_sales": stats["total_sales"] if stats else 0,
        "platform_fees": float(stats["platform_fees"]) if stats else 0.0,
        "net_revenue": float(stats["net_revenue"]) if stats else 0.0,
        "pending_payout": float(payout_row["pending"]) if payout_row else 0.0,
        "items_listed": items_row["cnt"] if items_row else 0,
        "avg_item_rating": float(profile["rating_avg"]) if profile else 0.0,
        "monthly_revenue": [],
        "top_items": top_items,
    }
