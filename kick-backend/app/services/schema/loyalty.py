"""Loyalty & Points System schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS loyalty_settings (
    channel TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    points_name TEXT NOT NULL DEFAULT 'Points',
    points_per_message INT NOT NULL DEFAULT 1,
    points_per_minute_watched INT NOT NULL DEFAULT 2,
    bonus_subscriber_multiplier FLOAT NOT NULL DEFAULT 2.0,
    bonus_follower_multiplier FLOAT NOT NULL DEFAULT 1.5,
    daily_bonus INT NOT NULL DEFAULT 50,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loyalty_points (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    balance INT NOT NULL DEFAULT 0,
    total_earned INT NOT NULL DEFAULT 0,
    total_spent INT NOT NULL DEFAULT 0,
    watch_time_minutes INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    last_daily_bonus TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS loyalty_rewards (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cost INT NOT NULL DEFAULT 100,
    type TEXT NOT NULL DEFAULT 'custom',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_redemptions INT,
    total_redemptions INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loyalty_redemptions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    reward_id TEXT NOT NULL,
    reward_name TEXT NOT NULL,
    cost INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""
