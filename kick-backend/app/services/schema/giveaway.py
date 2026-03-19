"""Giveaway & fraud detection schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS giveaways (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    keyword TEXT NOT NULL DEFAULT '!enter',
    status TEXT NOT NULL DEFAULT 'active',
    duration_seconds INT NOT NULL DEFAULT 300,
    max_entries INT,
    subscriber_only BOOLEAN NOT NULL DEFAULT FALSE,
    follower_only BOOLEAN NOT NULL DEFAULT FALSE,
    min_account_age_days INT NOT NULL DEFAULT 0,
    entries JSONB NOT NULL DEFAULT '[]',
    winner TEXT,
    created_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS giveaway_fraud_flags (
    id SERIAL PRIMARY KEY,
    giveaway_id TEXT NOT NULL,
    username TEXT NOT NULL,
    flag_type TEXT NOT NULL,
    matched_username TEXT,
    confidence FLOAT NOT NULL,
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    review_action TEXT,
    created_at TEXT NOT NULL
);
"""
