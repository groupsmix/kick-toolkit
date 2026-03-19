"""Anti-alt account detection schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS anti_alt_settings (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    min_account_age_days INT NOT NULL DEFAULT 7,
    auto_ban_threshold FLOAT NOT NULL DEFAULT 80.0,
    auto_timeout_threshold FLOAT NOT NULL DEFAULT 50.0,
    check_name_similarity BOOLEAN NOT NULL DEFAULT TRUE,
    check_follow_status BOOLEAN NOT NULL DEFAULT TRUE,
    whitelisted_users JSONB NOT NULL DEFAULT '[]',
    challenge_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    challenge_type TEXT NOT NULL DEFAULT 'follow',
    challenge_wait_minutes INT NOT NULL DEFAULT 10,
    challenge_message TEXT NOT NULL DEFAULT 'Please follow the channel and wait {minutes} minutes before chatting.',
    auto_whitelist_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    auto_whitelist_min_messages INT NOT NULL DEFAULT 100,
    auto_whitelist_min_follow_days INT NOT NULL DEFAULT 30
);

CREATE TABLE IF NOT EXISTS flagged_accounts (
    username TEXT PRIMARY KEY,
    risk_score FLOAT NOT NULL,
    risk_level TEXT NOT NULL,
    flags JSONB NOT NULL DEFAULT '[]',
    account_age_days INT NOT NULL DEFAULT 0,
    follower_count INT NOT NULL DEFAULT 0,
    is_following BOOLEAN NOT NULL DEFAULT FALSE,
    similar_names JSONB NOT NULL DEFAULT '[]',
    fingerprint_match_count INT NOT NULL DEFAULT 0,
    behavior_similarity_score FLOAT NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS banned_users (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    banned_at TEXT NOT NULL,
    ban_reason TEXT,
    ban_source TEXT NOT NULL DEFAULT 'manual',
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS user_fingerprints (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    fingerprint_hash TEXT,
    client_ip_hash TEXT,
    user_agent_hash TEXT,
    session_metadata JSONB NOT NULL DEFAULT '{}',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(username, channel)
);

CREATE TABLE IF NOT EXISTS behavior_profiles (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    message_count INT NOT NULL DEFAULT 0,
    avg_msg_length FLOAT NOT NULL DEFAULT 0,
    avg_typing_speed FLOAT NOT NULL DEFAULT 0,
    caps_ratio FLOAT NOT NULL DEFAULT 0,
    emoji_frequency FLOAT NOT NULL DEFAULT 0,
    emoji_profile JSONB NOT NULL DEFAULT '{}',
    vocab_fingerprint JSONB NOT NULL DEFAULT '{}',
    timing_histogram JSONB NOT NULL DEFAULT '{}',
    msg_length_stats JSONB NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS user_challenges (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    challenge_type TEXT NOT NULL,
    challenge_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    expires_at TEXT,
    completed_at TEXT,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS whitelisted_users (
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    added_by TEXT,
    reason TEXT,
    tier TEXT NOT NULL DEFAULT 'regular',
    auto_whitelisted BOOLEAN NOT NULL DEFAULT FALSE,
    message_count_at_whitelist INT NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (username, channel)
);

CREATE TABLE IF NOT EXISTS moderation_actions (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    channel TEXT NOT NULL,
    action TEXT NOT NULL,
    risk_score_at_action FLOAT,
    features JSONB NOT NULL DEFAULT '{}',
    performed_by TEXT NOT NULL DEFAULT 'system',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_model_weights (
    channel TEXT PRIMARY KEY,
    feature_weights JSONB NOT NULL DEFAULT '{}',
    training_samples INT NOT NULL DEFAULT 0,
    last_trained_at TEXT,
    model_version INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS raid_events (
    id SERIAL PRIMARY KEY,
    channel TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    new_chatters_count INT NOT NULL,
    window_seconds INT NOT NULL,
    suspicious_accounts JSONB NOT NULL DEFAULT '[]',
    auto_action_taken TEXT NOT NULL DEFAULT 'none',
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS raid_settings (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    new_chatter_threshold INT NOT NULL DEFAULT 20,
    window_seconds INT NOT NULL DEFAULT 60,
    auto_action TEXT NOT NULL DEFAULT 'none',
    min_account_age_days INT NOT NULL DEFAULT 7
);
"""
