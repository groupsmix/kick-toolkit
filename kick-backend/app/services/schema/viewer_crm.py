"""Viewer CRM schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS viewer_profiles (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    total_messages INT NOT NULL DEFAULT 0,
    streams_watched INT NOT NULL DEFAULT 0,
    is_subscriber BOOLEAN NOT NULL DEFAULT FALSE,
    is_follower BOOLEAN NOT NULL DEFAULT FALSE,
    segment TEXT NOT NULL DEFAULT 'new',
    watch_time_minutes INT NOT NULL DEFAULT 0,
    favorite_games JSONB NOT NULL DEFAULT '[]',
    notes TEXT NOT NULL DEFAULT '',
    UNIQUE(channel, username)
);
"""
