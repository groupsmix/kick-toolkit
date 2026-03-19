"""AI Clip Pipeline schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hype_moments (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    session_id TEXT,
    timestamp_start TEXT NOT NULL,
    timestamp_end TEXT NOT NULL,
    intensity FLOAT NOT NULL DEFAULT 0.0,
    trigger_type TEXT NOT NULL DEFAULT 'chat_spike',
    message_count INT NOT NULL DEFAULT 0,
    peak_rate FLOAT NOT NULL DEFAULT 0.0,
    sample_messages JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'detected',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generated_clips (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    hype_moment_id TEXT,
    title TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    file_path TEXT,
    thumbnail_path TEXT,
    duration_seconds FLOAT NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'pending',
    platform_specs JSONB NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clip_posts (
    id TEXT PRIMARY KEY,
    clip_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_post_id TEXT,
    post_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    caption TEXT NOT NULL DEFAULT '',
    error_message TEXT,
    posted_at TEXT,
    created_at TEXT NOT NULL
);
"""
