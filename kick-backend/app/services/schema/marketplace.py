"""Creator Economy Marketplace schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS seller_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT,
    website TEXT,
    total_sales INT NOT NULL DEFAULT 0,
    total_revenue FLOAT NOT NULL DEFAULT 0.0,
    rating_avg FLOAT NOT NULL DEFAULT 0.0,
    rating_count INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_items (
    id TEXT PRIMARY KEY,
    seller_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'overlay',
    price FLOAT NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'USD',
    preview_url TEXT,
    download_url TEXT,
    thumbnail_url TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    download_count INT NOT NULL DEFAULT 0,
    rating_avg FLOAT NOT NULL DEFAULT 0.0,
    rating_count INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_purchases (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    buyer_user_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    price_paid FLOAT NOT NULL DEFAULT 0.0,
    platform_fee FLOAT NOT NULL DEFAULT 0.0,
    seller_payout FLOAT NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'completed',
    payment_reference TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(item_id, buyer_user_id)
);

CREATE TABLE IF NOT EXISTS marketplace_reviews (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INT NOT NULL DEFAULT 5,
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(item_id, user_id)
);

CREATE TABLE IF NOT EXISTS seller_payouts (
    id TEXT PRIMARY KEY,
    seller_id TEXT NOT NULL,
    amount FLOAT NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'pending',
    payment_method TEXT NOT NULL DEFAULT 'stripe',
    payment_reference TEXT,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    created_at TEXT NOT NULL,
    paid_at TEXT
);
"""
