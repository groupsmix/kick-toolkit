"""Authentication & session schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    access_token TEXT,
    refresh_token TEXT,
    expires_in INT,
    token_type TEXT,
    scope TEXT,
    user_data JSONB NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT '',
    expires_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pending_auth (
    state TEXT PRIMARY KEY,
    code_verifier TEXT NOT NULL,
    session_id TEXT NOT NULL
);
"""
