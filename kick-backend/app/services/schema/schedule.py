"""Stream Schedule schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS stream_schedules (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    day_of_week INT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    game TEXT NOT NULL DEFAULT '',
    recurring BOOLEAN NOT NULL DEFAULT TRUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TEXT NOT NULL
);
"""
