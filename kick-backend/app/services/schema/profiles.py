"""Public Streamer Profile schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS streamer_profiles (
    channel TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT,
    banner_url TEXT,
    social_links JSONB NOT NULL DEFAULT '{}',
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    theme_color TEXT NOT NULL DEFAULT '#10b981',
    total_followers INT NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
"""
