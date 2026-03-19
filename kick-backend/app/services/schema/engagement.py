"""Chat Polls, Predictions & Voting schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS polls (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    title TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]',
    duration_seconds INT NOT NULL DEFAULT 300,
    allow_multiple_votes BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS poll_votes (
    id TEXT PRIMARY KEY,
    poll_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    option_index INT NOT NULL,
    voted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    title TEXT NOT NULL,
    outcomes JSONB NOT NULL DEFAULT '[]',
    lock_seconds INT NOT NULL DEFAULT 300,
    status TEXT NOT NULL DEFAULT 'open',
    winning_index INT,
    created_at TEXT NOT NULL,
    locked_at TEXT,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS prediction_bets (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    username TEXT NOT NULL,
    outcome_index INT NOT NULL,
    amount INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    payout INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""
