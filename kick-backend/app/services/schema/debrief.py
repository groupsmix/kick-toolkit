"""AI Post-Stream Debrief schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS debrief_results (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    session_id TEXT,
    summary TEXT NOT NULL DEFAULT '',
    top_moments JSONB NOT NULL DEFAULT '[]',
    sentiment_timeline JSONB NOT NULL DEFAULT '[]',
    chat_highlights JSONB NOT NULL DEFAULT '[]',
    recommendations JSONB NOT NULL DEFAULT '[]',
    title_suggestions JSONB NOT NULL DEFAULT '[]',
    trending_topics JSONB NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
"""
