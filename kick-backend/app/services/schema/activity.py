"""Activity / audit log schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activity_log_channel ON activity_log (channel);
"""
