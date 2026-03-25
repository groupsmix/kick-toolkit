"""Tournament schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tournaments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    game TEXT NOT NULL DEFAULT '',
    max_participants INT NOT NULL DEFAULT 16,
    format TEXT NOT NULL DEFAULT 'single_elimination',
    keyword TEXT NOT NULL DEFAULT '!join',
    status TEXT NOT NULL DEFAULT 'registration',
    participants JSONB NOT NULL DEFAULT '[]',
    matches JSONB NOT NULL DEFAULT '[]',
    current_round INT NOT NULL DEFAULT 0,
    winner TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS tournament_participants (
    id TEXT PRIMARY KEY,
    tournament_id TEXT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    seed INT,
    eliminated BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (tournament_id, username)
);

CREATE TABLE IF NOT EXISTS tournament_matches (
    id TEXT PRIMARY KEY,
    tournament_id TEXT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    round INT NOT NULL,
    match_number INT NOT NULL,
    player1 TEXT,
    player2 TEXT,
    winner TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS saved_ideas (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    estimated_cost TEXT NOT NULL DEFAULT 'Free',
    engagement_level TEXT NOT NULL DEFAULT 'medium',
    requirements JSONB NOT NULL DEFAULT '[]',
    saved BOOLEAN NOT NULL DEFAULT TRUE
);
"""
