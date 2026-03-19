"""Song Request System schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS song_queue_settings (
    channel TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    max_queue_size INT NOT NULL DEFAULT 50,
    max_duration_seconds INT NOT NULL DEFAULT 600,
    allow_duplicates BOOLEAN NOT NULL DEFAULT FALSE,
    subscriber_only BOOLEAN NOT NULL DEFAULT FALSE,
    cost_per_request INT NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS song_requests (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    artist TEXT NOT NULL DEFAULT '',
    url TEXT,
    platform TEXT NOT NULL DEFAULT 'youtube',
    duration_seconds INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued',
    position INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""
