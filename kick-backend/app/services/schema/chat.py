"""Chat logs schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chat_logs (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason TEXT
);
"""
