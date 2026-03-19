"""Chat bot configuration schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bot_configs (
    channel TEXT PRIMARY KEY,
    prefix TEXT NOT NULL DEFAULT '!',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    welcome_message TEXT,
    auto_mod_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    welcome_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    welcome_new_message TEXT,
    welcome_returning_message TEXT,
    welcome_subscriber_message TEXT,
    shoutout_template TEXT NOT NULL DEFAULT 'Check out {target} at kick.com/{target}! They were last playing {game}.',
    auto_shoutout_raiders BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS bot_commands (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    response TEXT NOT NULL,
    cooldown INT NOT NULL DEFAULT 5,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    mod_only BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(channel, name)
);

CREATE TABLE IF NOT EXISTS timed_messages (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    message TEXT NOT NULL,
    interval_minutes INT NOT NULL DEFAULT 15,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS moderation_rules (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    action TEXT NOT NULL DEFAULT 'delete',
    severity INT NOT NULL DEFAULT 1,
    settings JSONB NOT NULL DEFAULT '{}'
);
"""
