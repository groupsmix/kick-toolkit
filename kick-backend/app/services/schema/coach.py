"""AI Stream Coach schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS coach_settings (
    channel TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    engagement_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    game_duration_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    viewer_change_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    raid_welcome_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    sentiment_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    break_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    break_reminder_minutes INT NOT NULL DEFAULT 120,
    engagement_drop_threshold FLOAT NOT NULL DEFAULT 30.0,
    viewer_change_threshold INT NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS stream_sessions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    peak_viewers INT NOT NULL DEFAULT 0,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    total_messages INT NOT NULL DEFAULT 0,
    game TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS coach_suggestions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TEXT NOT NULL,
    dismissed_at TEXT
);

CREATE TABLE IF NOT EXISTS stream_snapshots (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    viewer_count INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    game TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);
"""
