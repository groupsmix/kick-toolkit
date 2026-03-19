"""Stream Intelligence Dashboard schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS stream_intel_sessions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_minutes INT NOT NULL DEFAULT 0,
    peak_viewers INT NOT NULL DEFAULT 0,
    avg_viewers FLOAT NOT NULL DEFAULT 0.0,
    chat_messages INT NOT NULL DEFAULT 0,
    new_followers INT NOT NULL DEFAULT 0,
    new_subscribers INT NOT NULL DEFAULT 0,
    stream_score FLOAT NOT NULL DEFAULT 0.0,
    game TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS stream_scores (
    channel TEXT PRIMARY KEY,
    overall_score FLOAT NOT NULL DEFAULT 0.0,
    viewer_score FLOAT NOT NULL DEFAULT 0.0,
    chat_score FLOAT NOT NULL DEFAULT 0.0,
    growth_score FLOAT NOT NULL DEFAULT 0.0,
    consistency_score FLOAT NOT NULL DEFAULT 0.0,
    trend TEXT NOT NULL DEFAULT 'stable',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS best_time_slots (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    day_of_week INT NOT NULL,
    hour INT NOT NULL,
    competition_score FLOAT NOT NULL DEFAULT 0.0,
    recommended_score FLOAT NOT NULL DEFAULT 0.0,
    avg_category_viewers INT NOT NULL DEFAULT 0,
    active_streamers INT NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(channel, day_of_week, hour)
);
"""
