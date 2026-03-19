"""Viewer Heatmap schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS viewer_sessions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    stream_session_id TEXT,
    username TEXT NOT NULL,
    joined_at TEXT NOT NULL,
    left_at TEXT,
    duration_seconds INT NOT NULL DEFAULT 0,
    messages_sent INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS content_segments (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    stream_session_id TEXT NOT NULL,
    label TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    viewer_count_start INT NOT NULL DEFAULT 0,
    viewer_count_end INT NOT NULL DEFAULT 0,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    retention_rate FLOAT NOT NULL DEFAULT 0.0,
    chat_activity INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS heatmap_snapshots (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    stream_session_id TEXT NOT NULL,
    minute_offset INT NOT NULL DEFAULT 0,
    viewer_count INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    unique_chatters INT NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);
"""
