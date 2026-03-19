"""Analytics & predictions schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS streamer_snapshots (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    peak_viewers INT NOT NULL DEFAULT 0,
    follower_count INT NOT NULL DEFAULT 0,
    subscriber_count INT NOT NULL DEFAULT 0,
    hours_streamed FLOAT NOT NULL DEFAULT 0.0,
    chat_messages INT NOT NULL DEFAULT 0,
    categories JSONB NOT NULL DEFAULT '[]',
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS growth_predictions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    metric TEXT NOT NULL,
    current_value FLOAT NOT NULL DEFAULT 0.0,
    predicted_value FLOAT NOT NULL DEFAULT 0.0,
    predicted_date TEXT NOT NULL DEFAULT '',
    confidence FLOAT NOT NULL DEFAULT 0.0,
    trend TEXT NOT NULL DEFAULT 'stable',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS growth_comparisons (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    compared_channel TEXT NOT NULL,
    similarity_score FLOAT NOT NULL DEFAULT 0.0,
    growth_phase TEXT NOT NULL DEFAULT '',
    insight TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS streamer_stock_scores (
    channel TEXT PRIMARY KEY,
    stock_score FLOAT NOT NULL DEFAULT 0.0,
    trend TEXT NOT NULL DEFAULT 'stable',
    change_pct FLOAT NOT NULL DEFAULT 0.0,
    rank INT NOT NULL DEFAULT 0,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    follower_count INT NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
"""
