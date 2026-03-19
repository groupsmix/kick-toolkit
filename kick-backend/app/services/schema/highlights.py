"""Auto-Highlight Detection schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS highlight_markers (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    session_id TEXT,
    timestamp_offset_seconds INT NOT NULL DEFAULT 0,
    intensity FLOAT NOT NULL DEFAULT 0.0,
    message_rate FLOAT NOT NULL DEFAULT 0.0,
    duration_seconds INT NOT NULL DEFAULT 30,
    description TEXT NOT NULL DEFAULT '',
    sample_messages JSONB NOT NULL DEFAULT '[]',
    category TEXT NOT NULL DEFAULT 'hype',
    created_at TEXT NOT NULL
);
"""
