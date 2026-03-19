"""Revenue Intelligence schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS revenue_entries (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    source TEXT NOT NULL,
    amount FLOAT NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'USD',
    description TEXT NOT NULL DEFAULT '',
    stream_session_id TEXT,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""
