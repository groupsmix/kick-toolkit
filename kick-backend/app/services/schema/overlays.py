"""OBS Overlay Widgets schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS overlay_settings (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    overlay_type TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    token TEXT NOT NULL DEFAULT '',
    config JSONB NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(channel, overlay_type)
);

CREATE TABLE IF NOT EXISTS alert_queue (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    displayed_at TEXT
);
"""
